#!/usr/bin/env python3
"""WEBSITE side of the 2026-10-16 security picks (sql/professify-security-picks-2026-10-16.sql). index.html only.
No build stamp (the coordinator stamps at merge). Every edit is one exact anchor that must occur exactly once.

(a) Classmate suggestions: the server now sends codes = {} for people who are not friends yet (they may know HOW MANY classes
    you share, not which). The card already falls back to the count; this makes that the stated contract: no chips, and
    "N classes in common" taken from `overlap` (singular for 1, "In one of your classes" if the count is missing).
(b) Trending professors: asks for a floor of 3 students (the server's floor is 3 and only signed-in students count), and the
    comment that said five / device pseudonyms is corrected.
(c) Website notifications: pushEnable saves through claim_push_subscription(...) (the endpoint belongs to whoever is signed in
    now; re-subscribing works). A database without that function keeps today's upsert.

Usage: python3 sec-picks-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'sec-picks (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---------------------------------------------------------------- (a) classmate cards: a count, never chips, for non-friends
one("""    /* codes only when the row really carries them — the card chips whatever is here and
       shows nothing when it is empty, rather than naming a class we cannot name.""",
    """    /* sec-picks (2026-10-16): for someone who is not a friend yet the server sends codes = [] and only the
       count (overlap): the card then reads "N classes in common" with no chips.
       codes only when the row really carries them — the card chips whatever is here and
       shows nothing when it is empty, rather than naming a class we cannot name.""")

# ---------------------------------------------------------------- (b) trending: floor of 3 students
one("""    var r=await sb.rpc('trending_profs',{p_limit:10,p_min:5});""",
    """    var r=await sb.rpc('trending_profs',{p_limit:10,p_min:3});   /* sec-picks (2026-10-16): 3 different signed-in students (the server's floor too) */""")
one("""AND IT HIDES ITSELF WHEN THERE IS NOT ENOUGH DATA. trending_profs() returns nothing below five
   viewers, and""",
    """AND IT HIDES ITSELF WHEN THERE IS NOT ENOUGH DATA. trending_profs() returns nothing below three
   different signed-in students (sec-picks, 2026-10-16: was five browsers), and""")
one("""database enforces that: the count is over distinct device pseudonyms.""",
    """database enforces that: the count is over distinct signed-in accounts (a salted
   hash of the account id; signed-out browsers are still logged but never counted).""")

# ---------------------------------------------------------------- (c) push: claim the endpoint through the rpc
one("""    var r=await sb.from('push_subscriptions').upsert({
      user_id:sbUser.id, endpoint:j.endpoint, p256dh:keys.p256dh, auth:keys.auth,
      ua:String(navigator.userAgent||'').slice(0,200)
    },{onConflict:'endpoint'});
    if(r.error){ try{""",
    """    /* sec-picks (2026-10-16): claim_push_subscription deletes another account's row for this endpoint and saves this one's
       (a plain upsert cannot: the old row is invisible to the new account, and re-subscribing had no UPDATE policy). A database
       without the function keeps the plain upsert below. */
    var ua=String(navigator.userAgent||'').slice(0,200);
    var r=await sb.rpc('claim_push_subscription',{p_endpoint:j.endpoint,p_p256dh:keys.p256dh,p_auth:keys.auth,p_ua:ua});
    if(r.error&&typeof rpcMissing==='function'&&rpcMissing(r.error)){
      r=await sb.from('push_subscriptions').upsert({
        user_id:sbUser.id, endpoint:j.endpoint, p256dh:keys.p256dh, auth:keys.auth, ua:ua
      },{onConflict:'endpoint'});
    }
    if(r.error){ try{""")

f.write_text(s)
print('patched', f)
