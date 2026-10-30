#!/usr/bin/env python3
"""Network resilience 2/4 (2026-10-30, stress test s3 P5 e401): an expired sign-in (401 PGRST301 / "JWT expired") was
recovered only when posting a review; everywhere else it showed "Couldn't load your profile" or a failed toast.

tcFetch now handles it for every supabase-js call: on a 401 that says the token expired it asks supabase-js for a
fresh session ONCE (auth.refreshSession, shared by every request that hit the same wall — one refresh for a launch's
whole wave of 401s, and none again for 10 s) and sends the original request again with the new access token. The
refresh's own request (/auth/v1/...) is never refreshed, so there is no recursion. A refresh the server refuses
(AuthApiError 4xx: refresh token revoked or not found) signs this device out (auth.signOut scope local; supabase-js
2.112 would otherwise keep a session whose expires_at is still ahead), and the existing onAuthStateChange takes the
student to sign-in; a refresh that fails for want of a network leaves the original 401 for the caller, as before.
Apply after net-1.

Usage: python3 net-2-jwt-refresh-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""async function tcFetch(input, init) {
  for (let i = 0; ; i++) {
    const r = await tcFetchOnce(input, init);
    if (r.status !== 401 || i >= JWT_FUTURE_WAIT.length) return r;
    let code = '';
    try { const j = await r.clone().json(); code = String((j && (j.code || j.error_code)) || ''); } catch (e) {}
    if (code !== 'PGRST303') return r;
    TC.jwtRetries = (TC.jwtRetries || 0) + 1;
    await new Promise(res => setTimeout(res, JWT_FUTURE_WAIT[i]));
  }
}""", """/* (2026-10-30) An expired token (401 PGRST301 / "JWT expired") is refreshed once — one refresh shared by every request
   that hit it, none again for 10 s — and the request goes again with the new token. The refresh's own call (/auth/v1/)
   is never refreshed. A refresh the server refuses signs the student out (supabase-js's SIGNED_OUT → sign-in). */
let tcRf = null, tcRfAt = 0;
function tcRefreshTok() {
  const sb = TC.sb; if (!sb) return Promise.resolve(null);
  if (!tcRf || Date.now() - tcRfAt > 10000) {
    tcRfAt = Date.now(); TC.jwtRefreshes = (TC.jwtRefreshes || 0) + 1;
    tcRf = sb.auth.refreshSession().then(x => {
      if (x && !x.error && x.data && x.data.session && x.data.session.access_token) return x.data.session.access_token;
      /* the server refused the refresh token (not a network failure): this sign-in is over. supabase-js keeps a session
         whose expires_at is still ahead, so drop it here — SIGNED_OUT takes the student to sign-in. */
      const e = x && x.error;
      if (e && e.name === 'AuthApiError' && e.status >= 400 && e.status < 500) sb.auth.signOut({ scope: 'local' }).catch(() => {});
      return null;
    }, () => null);
  }
  return tcRf;
}
async function tcFetch(input, init) {
  let refreshed = /\\/auth\\/v1\\//.test(tcFetchUrl(input));
  for (let i = 0; ; i++) {
    const r = await tcFetchOnce(input, init);
    if (r.status !== 401) return r;
    let code = '', msg = '';
    try { const j = await r.clone().json(); code = String((j && (j.code || j.error_code)) || ''); msg = String((j && (j.message || j.msg)) || ''); } catch (e) {}
    if (code === 'PGRST303' && i < JWT_FUTURE_WAIT.length) {
      TC.jwtRetries = (TC.jwtRetries || 0) + 1;
      await new Promise(res => setTimeout(res, JWT_FUTURE_WAIT[i])); continue;
    }
    if (!refreshed && (code === 'PGRST301' || /jwt expired|token is expired/i.test(msg))) {
      refreshed = true;
      const tok = await tcRefreshTok();
      if (tok) {
        const h = new Headers((init && init.headers) || (input && typeof input === 'object' && input.headers) || {});
        h.set('Authorization', 'Bearer ' + tok);
        init = Object.assign({}, init, { headers: h }); continue;
      }
    }
    return r;
  }
}""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'net-2 jwt refresh: ok')
