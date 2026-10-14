#!/usr/bin/env python3
"""A friend's registration day on their page (Tate, 2026-10-14; the phone's registration-day-2026-10-11, "A friend's
page: Registers Wed, Oct 21 · 8a · 2 days before you", under the header strip of friend-header-strip-2026-10-10).

The website already loads friends' days (friend_registration_days('2274'), RUN 17) for Plans' and Home's cards. The friend's
profile (openFriendProfile) now shows theirs in its header, under the name line:

    Registers Wed, Oct 21, 2026 · 8a · 2 days before you        (a day of yours is set)
    Registers Wed, Oct 21, 2026 · 8a                            (yours isn't: nothing to compare with)
    Registers today at 8a                                      (their day is today)

- Only when they shared one and it is still to come (today or later, Pacific); nothing at all otherwise (no "not shared",
  no empty line): a friend who didn't share, a day that has passed, a missing RUN 17 table / function, a failed load.
- Only while registering is the thing you're doing (the same rule as the cards: signed in, the term you choose in is the
  registration term, up to Round 1's last day) and only for an accepted friend you haven't blocked: the same rows the
  cards list (TCReg.rows), never a non-friend's day.
- The day has its year (the site writes dates with their year); the time is written like the cards' ("8a", "8:30a").
- It fills in by itself: opening a page asks for the days when the list is stale (2 minutes, as the cards do), and a list
  that arrives while the page is open (or a day of yours you then set, which moves "before you") redraws the line.
- Reads nothing new and writes nothing: no grade, no EMPLID, nothing about a non-friend is stored.

Usage: python3 website-friend-regday-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-friend-regday (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# 1. the line, in the registration-day module (it owns the rows, the term rule and the wording)
one("""  /* ---------------------------------------------------------------- the card */
  var ICON =""",
    """  /* ---------------------------------------------------------------- a friend's page (website-friend-regday, 2026-10-14) */
  /* "Registers Wed, Oct 21, 2026 · 8a · 2 days before you" — the phone's line on a friend's page. Nothing unless they shared a
     day that is still to come; never a day for someone who isn't an accepted, unblocked friend (frRows). */
  function dayYear(d) {
    try { return new Date(d + 'T12:00:00Z').toLocaleDateString('en-US', { timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }); } catch (_) { return d; }
  }
  function friendRowInner(id) {
    if (!active()) return '';
    var x = frRows().filter(function (r) { return r.id === id; })[0], td = today();
    if (!x || x.day < td) return '';
    var t = timeText(x.time), r = x.day === td ? '' : rel(x.day);
    var when = x.day === td ? 'Registers today' + (t ? ' at ' + t : '') : 'Registers ' + dayYear(x.day) + (t ? ' \\u00b7 ' + t : '');
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4.5" width="18" height="16" rx="2.5"/><path d="M3 9h18M8 2.5v4M16 2.5v4"/></svg>'
      + '<span class="rg-frt"><b>' + esc(when) + '</b>' + (r ? ' \\u00b7 ' + esc(r) : '') + '</span>';
  }
  function friendRowHtml(id) {
    if (active() && !RG.frBusy) setTimeout(function () { loadFriends(); }, 0);
    return '<div class="rg-frrow" data-rg-fr="' + esc(id) + '">' + friendRowInner(id) + '</div>';
  }

  /* ---------------------------------------------------------------- the card */
  var ICON =""")

# 2. a list that arrives (or a day of yours that is set) redraws the line on an open page
one("""    try { if (typeof renderCampusBanner === 'function') renderCampusBanner(); } catch (_) {}
    try { if (M) paintModal(); } catch (_) {}""",
    """    try { var fr = document.querySelectorAll('.rg-frrow'); for (var j = 0; j < fr.length; j++) fr[j].innerHTML = friendRowInner(fr[j].getAttribute('data-rg-fr')); } catch (_) {}   /* website-friend-regday (2026-10-14) */
    try { if (typeof renderCampusBanner === 'function') renderCampusBanner(); } catch (_) {}
    try { if (M) paintModal(); } catch (_) {}""")
one("""save: saveMine, timeText: timeText };""", """save: saveMine, timeText: timeText, friendRow: friendRowHtml };""")

# 3. the friend's page header
one("""        ${frEmailRow(f)}
      </div>
    </div>
    <div class="frp-tabs">""",
    """        ${frEmailRow(f)}
        ${(window.TCReg&&TCReg.friendRow)?TCReg.friendRow(f.id):''}
      </div>
    </div>
    <div class="frp-tabs">""")

# 4. styles
one(""".rg-more,.rg-miss{font-size:12.5px;font-weight:600;color:var(--text-2);padding:4px 6px}""",
    """.rg-more,.rg-miss{font-size:12.5px;font-weight:600;color:var(--text-2);padding:4px 6px}
/* website-friend-regday (2026-10-14): the line under a friend's name */
.rg-frrow{display:flex;align-items:center;gap:7px;margin-top:6px;font-size:13px;font-weight:600;color:var(--text-2);line-height:1.35}
.rg-frrow:empty{display:none}
.rg-frrow svg{flex:none;width:15px;height:15px}
.rg-frrow b{font-weight:700;color:var(--text)}""")

f.write_text(s)
print('patched', f)
