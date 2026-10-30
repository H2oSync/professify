#!/usr/bin/env python3
"""Network resilience 1/4 (2026-10-30, stress test s3 P4/P1): one request that never answers left the app loading forever,
and a lost connection at launch needed a "Try again" tap.

- tcFetch (the fetch every supabase-js call goes through) gives each attempt a deadline: 15 s for the database and
  auth, 2 minutes for storage uploads and edge functions (an avatar or share card on a slow phone). The caller's own
  AbortSignal still works. A deadline fails as "Failed to fetch (timed out)", so everything that already reads a
  network failure (the "Can't reach TermChamp" screen, toasts) reads it as one. Realtime is a WebSocket, not fetch:
  untouched. The seat feed, the catalog and Champ's ask call use window.fetch directly: untouched.
- loadAll waits with Promise.allSettled: one loader that fails no longer stops TC.ready (every loader already keeps
  its own error).
- "Can't reach TermChamp" / "Couldn't load your profile" retry on their own: on the window 'online' event, when the
  app comes back to the front (visibilitychange), and on Capacitor's appStateChange when the App plugin is in the
  build. With supabase-js itself missing (the script never loaded, web only) that is a page reload, which is what
  "Try again" did.

Usage: python3 net-1-timeouts-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""const JWT_FUTURE_WAIT = [600, 1200, 2000, 3200];
async function tcFetch(input, init) {
  for (let i = 0; ; i++) {
    const r = await fetch(input, init);
""", """const JWT_FUTURE_WAIT = [600, 1200, 2000, 3200];
/* (2026-10-30) No request waits forever: one hung read (profile, chats, plans) kept the app on its spinner for good.
   Each attempt gets a deadline — 15 s for the database and sign-in, 2 minutes for storage uploads and edge functions —
   and fails as a network failure, which every screen already knows how to say. The caller's own signal still aborts. */
const TC_FETCH_MS = 15000, TC_FETCH_LONG_MS = 120000;
const tcFetchUrl = input => String(typeof input === 'string' ? input : (input && input.url) || input || '');
function tcFetchOnce(input, init) {
  if (typeof AbortController !== 'function') return fetch(input, init);
  const own = (init && init.signal) || (input && typeof input === 'object' && input.signal) || null;
  if (own && own.aborted) return fetch(input, init);
  const ctl = new AbortController(); let late = false;
  if (own) own.addEventListener('abort', () => { try { ctl.abort(own.reason); } catch (e) { ctl.abort(); } }, { once: true });
  const ms = /\\/(storage|functions)\\/v1\\//.test(tcFetchUrl(input)) ? TC_FETCH_LONG_MS : TC_FETCH_MS;
  const t = setTimeout(() => { late = true; ctl.abort(); }, ms);   /* left running after the headers: it covers the body too */
  return fetch(input, Object.assign({}, init, { signal: ctl.signal })).catch(e => { clearTimeout(t); if (late) throw new TypeError('Failed to fetch (timed out)'); throw e; });
}
async function tcFetch(input, init) {
  for (let i = 0; ; i++) {
    const r = await tcFetchOnce(input, init);
""")

one("""  await Promise.all([loadMine(), loadFriends().then(v => { loadPins().catch(() => {}); return v; }), loadSaved().catch(() => {}), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads()), loadAudit(), loadPrefs(), loadRegDay(), loadCommits(), loadFriendBusy()]);""",
    """  /* allSettled (2026-10-30): one loader that fails must not keep the rest of the app from being ready */
  await Promise.allSettled([loadMine(), loadFriends().then(v => { loadPins().catch(() => {}); return v; }), loadSaved().catch(() => {}), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads()), loadAudit(), loadPrefs(), loadRegDay(), loadCommits(), loadFriendBusy()]);""")

one("""document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && TC.ready && Date.now() - (TC.loadedAt || 0) > 120000) { TC.loadedAt = Date.now(); TC.refresh(); loadSeats(); } });
""", """document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && TC.ready && Date.now() - (TC.loadedAt || 0) > 120000) { TC.loadedAt = Date.now(); TC.refresh(); loadSeats(); } });
/* (2026-10-30) "Can't reach TermChamp" and "Couldn't load your profile" try again by themselves when the phone is back
   online or the app comes back to the front — nobody should have to find the Try again button. No supabase-js at all
   (the script never loaded: web only, the iPhone app carries it) is a reload, exactly what Try again does. */
let tcWakeAt = 0;
function tcWake() {
  if (TC.phase !== 'offline' && TC.phase !== 'profileerr') return;
  if (!TC.client()) { if (navigator.onLine !== false && Date.now() - tcWakeAt > 5000) { tcWakeAt = Date.now(); location.reload(); } return; }
  if (TC.user) TC.load(); else TC.boot();
}
window.addEventListener('online', () => tcWake());
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') tcWake(); });
try { const AP = window.Capacitor && Capacitor.Plugins && Capacitor.Plugins.App; if (AP && AP.addListener) AP.addListener('appStateChange', st => { if (st && st.isActive) tcWake(); }); } catch (e) {}
""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'net-1 timeouts: ok')
