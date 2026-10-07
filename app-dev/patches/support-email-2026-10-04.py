#!/usr/bin/env python3
"""The contact email in the app becomes support@termchamp.com (Tate, 2026-10-04:
"make the email in help the support@termchamp.com").

1. LEGAL_CONTACT, the only address the app showed anyone, was Tate's personal iCloud address. The
   Terms, the Privacy Policy, the Security page and the Community Guidelines all print it
   ("Questions: …", "Want a copy of your data … Email …", "If a review about you is abusive …
   email …"), on the phone (Settings > Legal, and the sign-up links) and on the desktop. It is now
   support@termchamp.com, an alias of tatesims@termchamp.com on Spacemail set up the same day, so
   the mail still reaches Tate. It changes in both places it lives: the desktop's index.html, and
   app/planner.js, which carries the same legal pages lifted out of index.html.
2. Three places said "email us" and gave no address. They now name it:
   - the Privacy Policy's under-13 line (desktop and phone), through LEGAL_CONTACT;
   - the desktop's two "we'll delete it by hand" messages when Delete account fails. The first
     sits in DB_ERR_MSG, which runs before LEGAL_CONTACT is defined, so both use the literal.

The "Last updated" dates stay as they are: a contact address doesn't change what the documents say
about anyone's data or rules (the Privacy Policy moves its date when "what is collected or who can
see it changes").

Every file is read and checked before any is written, so the patch applies whole or not at all.
Applies after feed-class-recs-2026-10-04.py (build 19:00). First cut on 18:30, re-applied unchanged on 18:45, then on 19:00.
Usage: python3 support-email-2026-10-04.py <repo-dir>   (edits index.html and app/planner.js)
"""
import sys, os
ADDR = 'support@termchamp.com'
CONTACT = ("var LEGAL_CONTACT='tdogtate@icloud.com';", f"var LEGAL_CONTACT='{ADDR}';")
UNDER13 = ("If you believe someone under 13 has an account, email us and it will be removed.",
           "If you believe someone under 13 has an account, email <b>'+LEGAL_CONTACT+'</b> and it will be removed.")
EDITS = {
    'index.html': [
        CONTACT, UNDER13,
        ("try again, or email us and we’ll do it by hand.'",
         f"try again, or email {ADDR} and we’ll do it by hand.'"),
        ("'Account deletion isn’t switched on for this deploy yet — email us and we’ll do it by hand.'",
         f"'Account deletion isn’t switched on for this deploy yet — email {ADDR} and we’ll do it by hand.'"),
    ],
    os.path.join('app', 'planner.js'): [CONTACT, UNDER13],
}
out = {}
for rel, edits in EDITS.items():
    p = os.path.join(sys.argv[1], rel)
    s = open(p, encoding='utf-8').read()
    if all(s.count(a) == 0 and s.count(b) == 1 for a, b in edits):
        print('already patched', rel); continue
    for a, b in edits:
        n = s.count(a)
        if n != 1: sys.exit(f'{rel}: anchor matched {n}x: {a[:60]}')
        s = s.replace(a, b)
    if 'tdogtate@' in s: sys.exit(f'{rel}: the old address is still in the file')
    out[p] = s
for p, s in out.items():
    open(p, 'w', encoding='utf-8').write(s)
    print('patched', p)
print(len(out), 'file(s) changed')
