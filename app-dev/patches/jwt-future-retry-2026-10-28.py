#!/usr/bin/env python3
"""Tate, 2026-10-28: a friend making an account got "Couldn't load your profile · Error PGRST303 ·
JWT issued at future". The database refuses a sign-in token stamped a moment ahead of its own clock
(Supabase's sign-in and database servers can disagree by a second or two right after sign-up). The
request never ran, so it is always safe to send again. Every request through the app's database
client now waits and retries a PGRST303 up to 4 times (about 7 seconds in all) before the screen ever
sees an error."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""    flowType: 'pkce' } });
  TC.sb.auth.onAuthStateChange(""", """    flowType: 'pkce' }, global: { fetch: tcFetch } });
  TC.sb.auth.onAuthStateChange(""")
one("""TC.client = function () {
  if (TC.sb) return TC.sb;""", """/* A token "issued at future" (PGRST303) is refused before anything runs, so it is always safe to send
   again; it clears within a second or two (2026-10-28, a friend's first sign-in). Anything else passes
   through untouched. */
const JWT_FUTURE_WAIT = [600, 1200, 2000, 3200];
async function tcFetch(input, init) {
  for (let i = 0; ; i++) {
    const r = await fetch(input, init);
    if (r.status !== 401 || i >= JWT_FUTURE_WAIT.length) return r;
    let code = '';
    try { const j = await r.clone().json(); code = String((j && (j.code || j.error_code)) || ''); } catch (e) {}
    if (code !== 'PGRST303') return r;
    TC.jwtRetries = (TC.jwtRetries || 0) + 1;
    await new Promise(res => setTimeout(res, JWT_FUTURE_WAIT[i]));
  }
}
TC.client = function () {
  if (TC.sb) return TC.sb;""")
p.write_text(s); print('jwt-future-retry applied')
