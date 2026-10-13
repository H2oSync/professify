#!/usr/bin/env python3
"""A friend's page: Message takes the pin's place and the pin is gone (Tate, 2026-10-08, on 19:15's card:
"dont make message so large it could also replace the pin and just take the pin away").

Message is a round pink chat button (44px, like your pencil) at the top right of the card, where your own profile has
the pencil. No full-width Message under the bubbles. The pin is no longer on a friend's page (stories are
still pinned by holding them). Unblock / Accept request / Add friend / Requested keep their row in the card.

Usage: python3 friend-message-in-pin-spot-2026-10-08.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'friend-message-in-pin-spot (2026-10-08)' in s:
    sys.exit('already patched')
def one(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:90]); s = s.replace(old, new)
one("""${isF && !bl ? pinBtn(id, 'fpin mepin') : ''}</div>""",
    """${isF && !bl ? `<button class="pbtn pink fmsg" data-a="openChatWith" data-x="${id}" aria-label="Message ${esc(p.short)}">${ic('msg', 20, 2.3)}</button>` : ''}</div>""")
one(""": isF ? `<button class="pbtn pink" data-a="openChatWith" data-x="${id}">Message</button>` : rel === 'incoming'""",
    """: isF ? '' : rel === 'incoming'""")
one(""".fact{display:flex}""", """.fact{display:flex}
.fact:empty{display:none}
/* friend-message-in-pin-spot (2026-10-08): Message where your profile has the pencil */
.fpg .fmsg{display:grid;place-items:center;width:44px;height:44px;padding:0;border-radius:22px;flex:none;align-self:center}
.fpg .fmsg svg{flex:none}""")
f.write_text(s); print('patched', f)
