#!/usr/bin/env python3
"""Network resilience 4/4 (2026-10-30, stress test s5): every return to the front after 2+ minutes downloaded the whole
seat feed again (the full term, paged) and, in the iPhone app, registered for push twice — pushInit's own
visibilitychange listener and pushAfterLoad at the end of the refresh — so register_push_token ran twice per resume.

- The foreground refresh keeps plans, messages, friends and the rest, but downloads course_seats only when the copy
  it has is 10 minutes old or more (TC.seatsAt: the last good download, or the cache's age at launch).
- Push registers at most once a minute (once per resume): launch still registers, as Apple wants, and a permission
  just turned on (in iPhone Settings, or the Turn on notifications button) always registers.

Usage: python3 net-4-resume-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && TC.ready && Date.now() - (TC.loadedAt || 0) > 120000) { TC.loadedAt = Date.now(); TC.refresh(); loadSeats(); } });""",
    """/* (2026-10-30) the seat feed is the whole term: downloaded again only when what we have is 10 minutes old */
const SEATS_FRESH_MS = 600000;
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && TC.ready && Date.now() - (TC.loadedAt || 0) > 120000) { TC.loadedAt = Date.now(); TC.refresh(); if (!TC.seatsAt || TC.err.seats || Date.now() - TC.seatsAt >= SEATS_FRESH_MS) loadSeats(); } });""")

one("""async function pushRegister() { const p = PUSH.plug(); if (!p) return; try { await p.register(); } catch (e) {} }""",
    """/* (2026-10-30) once per resume: pushInit's foreground listener and pushAfterLoad (end of the refresh) both ask; one goes.
   force = a permission just granted. */
async function pushRegister(force) { const p = PUSH.plug(); if (!p) return; if (!force && Date.now() - (PUSH.regAt || 0) < 60000) return; PUSH.regAt = Date.now(); try { await p.register(); } catch (e) {} }""")

one("""const was = PUSH.state; pushPerm().then(st => { if (st === 'granted') pushRegister(); if (st !== was) render(true); }); });""",
    """const was = PUSH.state; pushPerm().then(st => { if (st === 'granted') pushRegister(was !== 'granted' && was !== 'unknown'); if (st !== was) render(true); }); });""")

one("""if (r.receive === 'granted') { await pushRegister(); toast(""", """if (r.receive === 'granted') { await pushRegister(true); toast(""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'net-4 resume: ok')
