#!/usr/bin/env python3
"""Tate, 2026-10-29: some students never enter their code (Resend shows it delivered, so it's in Junk),
and one tapped Resend four times in 45s and got rate-limit errors. On the phone app's code screen:
a "Not there? Check Junk" line naming the sender; the code-login screen waits the same 60s as sign-up
(it was 45s, but Supabase allows one code per 60s); a refused resend reads the wait Supabase gives and
counts down from it, instead of "there's an hourly limit"."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
# 1. the Junk hint, right under "We sent a 6-digit code to …"
one("""<div><button type="button" class="pill-pink" data-a="onbBack">Edit email</button></div></div>""",
    """<p id="junkHint" style="margin:0;font-size:13.5px;line-height:1.45;font-weight:700;color:var(--muted)">Not there? Check your <b>Junk</b> or <b>Spam</b> folder for “Your TermChamp code” from noreply@termchamp.com.</p><div><button type="button" class="pill-pink" data-a="onbBack">Edit email</button></div></div>""")
# 2. code log-in waits 60s like sign-up (Supabase: one code per address per 60s)
one("""Object.assign(UI.signin, { mode: 'verify', err: '', note: '', resendAt: Date.now() + 45000 }); render();""",
    """Object.assign(UI.signin, { mode: 'verify', err: '', note: '', resendAt: Date.now() + 60000 }); render();""")
# 3. a refused resend: count down from the wait Supabase names
one("""    if (err) si.err = authFriendlyErr(err); else { si.note = 'New code sent. The older one stops working.'; si.resendAt = Date.now() + 60000; }""",
    """    if (err) { const w = /after (\\d+) second/i.exec(String(err)); si.err = authFriendlyErr(err); if (w) si.resendAt = Date.now() + (Number(w[1]) + 1) * 1000; }
    else { si.note = 'New code sent. The older one stops working. Check Junk too.'; si.resendAt = Date.now() + 60000; }""")
# 4. the rate-limit message says how long, not "hourly limit"
one("""  if(/rate limit|too many requests|only request this after|429/i.test(m))
    return 'Too many codes requested just now — there’s an hourly limit on verification emails. Wait a minute and hit resend.';""",
    """  var wait=/after (\\d+) second/i.exec(m);
  if(wait) return 'A code was just sent — wait '+wait[1]+' seconds before asking for another. Check your Junk folder too.';
  if(/rate limit|too many requests|only request this after|429/i.test(m))
    return 'Too many codes requested just now. Wait a minute, check your Junk folder, then tap Resend.';""")
p.write_text(s); print('code-junk-hint applied (app)')
