#!/usr/bin/env python3
"""Tate, 2026-10-29, website (index.html) half of the code-email fix: the resend button waited 45s
(20s after a failed send) but Supabase allows one code per address per 60s, which is how one student
got four rate-limit errors in 45 seconds. Now 60s, a refused resend waits the seconds Supabase names,
and the code step says to check Junk and who the email is from."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""    +'<p class="auth-sub">We emailed a verification code to <b>'+escapeHtml(email)+'</b>.</p>'""",
    """    +'<p class="auth-sub">We emailed a verification code to <b>'+escapeHtml(email)+'</b>.</p>'
    +'<p class="auth-sub" id="authJunk" style="margin-top:-4px;font-size:13px">Not there? Check your <b>Junk</b> or <b>Spam</b> folder for \\u201cYour TermChamp code\\u201d from noreply@termchamp.com.</p>'""")
one("""  setTimeout(function(){var c=document.getElementById('authCode');if(c)c.focus();},50);
  authResendCooldown(45);""",
    """  setTimeout(function(){var c=document.getElementById('authCode');if(c)c.focus();},50);
  authResendCooldown(60);""")
one("""    if(note)note.innerHTML='New code sent to <b>'+escapeHtml(email)+'</b>. The older one stops working.';
    authResendCooldown(45);
  }catch(e){
    authErr(e&&e.message,'Could not resend the code. Try again in a minute.');
    authResendCooldown(20);""",
    """    if(note)note.innerHTML='New code sent to <b>'+escapeHtml(email)+'</b>. The older one stops working.';
    authResendCooldown(60);
  }catch(e){
    authErr(e&&e.message,'Could not resend the code. Try again in a minute.');
    var w=/after (\\d+) second/i.exec(String(e&&e.message||''));
    authResendCooldown(w?Number(w[1])+1:60);""")
one("""  if(/rate limit|too many requests|only request this after|429/i.test(m))
    return 'Too many codes requested just now — there’s an hourly limit on verification emails. Wait a minute and hit resend.';
  if(/signups not allowed|Signups not allowed/i.test(m))
    return 'New sign-ups are switched off for this project right now.';
  if(/invalid|malformed/i.test(m)&&/email/i.test(m))""",
    """  var wait=/after (\\d+) second/i.exec(m);
  if(wait) return 'A code was just sent \\u2014 wait '+wait[1]+' seconds before asking for another. Check your Junk folder too.';
  if(/rate limit|too many requests|only request this after|429/i.test(m))
    return 'Too many codes requested just now. Wait a minute, check your Junk folder, then tap Resend.';
  if(/signups not allowed|Signups not allowed/i.test(m))
    return 'New sign-ups are switched off for this project right now.';
  if(/invalid|malformed/i.test(m)&&/email/i.test(m))""")
p.write_text(s); print('web code-junk-hint applied (index.html)')
