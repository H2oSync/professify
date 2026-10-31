#!/usr/bin/env python3
"""Privacy Policy (termchamp.com/privacy is built from LEGAL_DOCS.privacy in app/planner.js, which the iPhone app also
shows; the website's root index.html carries the same block). Run on both files: Connect contacts
(iPhone app 1.0.2) and the optional phone number replace "No phone number, in any form"."""
import sys, pathlib, re
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("var LEGAL_UPDATED_PRIVACY='6 October 2026';", "var LEGAL_UPDATED_PRIVACY='30 October 2026';")
# the old bullet, whole line
m = re.search(r"    \+'<li><b>No phone number, in any form\.</b>.*?</li>'\n", s)
assert m and s.count('No phone number, in any form') == 1
s = s[:m.start()] + (
"    +'<li><b>Your phone number \\u2014 only if you add it.</b> It is optional (at sign-up, or in Settings \\u203a Contacts in the iPhone app) "
"and lets friends who have your number saved find you. It is never stored as a number: the app turns it into a one-way code on your phone, "
"and the server scrambles that again with a secret key kept in the database\\u2019s vault, which the app and this site never see. "
"It is never shown on your profile or to anyone, one number can belong to only one account, and you can remove it in Settings at any time. "
"(An earlier version of contact matching was retired on 7 September because its hashing used a prefix visible in the page source; this one does not.)</li>'\n"
) + s[m.end():]
one("""    +'<h4>Notifications</h4>'""",
"""    +'<h4>Find friends from your contacts (iPhone app)</h4>'
    +'<p>Only if you tap <b>Connect contacts</b> and allow it in iOS. The app reads the phone numbers and email addresses in your contacts <b>on your phone</b>, turns each one into a one-way code there, and sends only those codes to TermChamp\\u2019s server. The server compares them with students at your school and sends back who matched, so you can add them; the names in your contacts never leave your phone.</p>'
    +'<p><b>Your address book is not stored.</b> The codes are compared and forgotten \\u2014 no names, numbers, emails or codes from your contacts are kept, and nobody is told that you looked them up. Only students at your school can match, never anyone you have blocked or who has blocked you, and never an account being deleted. Each account can check contacts a limited number of times an hour and a day, so the feature cannot be used to test lists of numbers.</p>'
    +'<p>Being straight about the limit: a one-way code of a phone number or email can in principle be worked out by someone who tries every possible number. That is why the codes your phone sends are never kept, and why the number you add yourself is scrambled again with a key only the server holds. Turn it off any time in Settings \\u203a Contacts, or in your iPhone\\u2019s Settings \\u203a TermChamp \\u203a Contacts.</p>'
    +'<h4>Notifications</h4>'""")
p.write_text(s); print(p, 'privacy: contacts + phone number')
# Security page, "What we do not do" (same file)
s = p.read_text()
one("""    +'<li>No phone numbers, and passwords only as a hash.</li>'""",
    """    +'<li>No phone numbers in readable form: one you add for Connect contacts is kept only as a keyed one-way code, and contacts you check are compared and forgotten. Passwords only as a hash.</li>'""")
p.write_text(s); print(p, 'security: phone numbers line')
