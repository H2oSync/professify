#!/usr/bin/env python3
"""Tate, 2026-10-30: "i dont want people bombarded". Limits on the two pop-ups (run after
pushask-popup, contacts and contacts-into-popqueue):
  · at most ONE pop-up a day (any pop-up: on an app open or right after a tap). The one exception is the
    end of sign-up, which keeps both (notifications, then contacts) — Tate: "have both at end of sign up".
  · "Connect contacts" asks at most 3 times in all (30 days apart), then never again.
  · "Notifications are off · Open Settings" shows at most 2 times in all, then never again.
The Contacts button, Settings › Contacts and Settings › Notifications always work."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)

# the day + the caps
one("""const PUSH_ASK_MAX = 3, PUSH_OFF_EVERY = 30 * 864e5, POP_AWAY = 30 * 60000;""",
    """const PUSH_ASK_MAX = 3, PUSH_OFF_EVERY = 30 * 864e5, POP_AWAY = 30 * 60000;
/* (2026-10-30) one pop-up a day, and caps: "Notifications are off" twice in all, "Connect contacts" three times */
const POP_DAY_KEY = 'tc_pop_day', PUSH_OFFN_KEY = 'tc_push_off_n', PUSH_OFF_MAX = 2, CT_ASK_MAX = 3;
function popToday() { const d = new Date(); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
function popDayUsed() { try { return localStorage.getItem(POP_DAY_KEY) === popToday(); } catch (e) { return false; } }
function popMarkDay() { try { localStorage.setItem(POP_DAY_KEY, popToday()); } catch (e) {} }""")

# the queue (app opens) skips a day that already had one; the end of sign-up is exempt
one("""  if (at === 'onboarding') return true;
  const st = S.stack[S.tab] || [];""", """  if (at === 'onboarding') return true;
  if (popDayUsed()) return false;
  const st = S.stack[S.tab] || [];""")

# every notifications pop-up marks the day; "off" counts toward its cap
one("""  if (reason === 'off') lsSet(PUSH_OFF_KEY, Date.now());""",
    """  popMarkDay();
  if (reason === 'off') { lsSet(PUSH_OFF_KEY, Date.now()); lsSet(PUSHOFFN_PLACEHOLDER, lsNum(PUSHOFFN_PLACEHOLDER) + 1); }""".replace('PUSHOFFN_PLACEHOLDER', 'PUSH_OFFN_KEY'))
one("""    if (st === 'denied') return Date.now() - lsNum(PUSH_OFF_KEY) >= PUSH_OFF_EVERY ? 'off' : null;""",
    """    if (st === 'denied') return lsNum(PUSH_OFFN_KEY) < PUSH_OFF_MAX && Date.now() - lsNum(PUSH_OFF_KEY) >= PUSH_OFF_EVERY ? 'off' : null;""")

# right after a tap (watch a seat, send a chat, unmute): not on a day that already had a pop-up
one("""  const st = await pushPerm();
  if (UI.sheet || UI.champ) return;
  if (st === 'denied') {""", """  const st = await pushPerm();
  if (UI.sheet || UI.champ || popDayUsed()) return;
  if (st === 'denied') {
    if (lsNum(PUSH_OFFN_KEY) >= PUSH_OFF_MAX) return;""")

# contacts: three asks in all; marks the day; the sign-up one may follow the notifications one
one("""  const st = ctState(); if (st.on || Date.now() < (+st.snooze || 0)) return false;
  ctSet({ snooze: Date.now() + CT_SNOOZE, asked: Date.now(), why });""",
    """  const st = ctState(); if (st.on || Date.now() < (+st.snooze || 0) || (+st.k || 0) >= CT_ASK_MAX) return false;
  if (why !== 'onboarding' && popDayUsed()) return false;
  ctSet({ snooze: Date.now() + CT_SNOOZE, asked: Date.now(), why, k: (+st.k || 0) + 1 }); popMarkDay();""")
one("""    return (+st.n || 0) >= 2 && !st.on && Date.now() >= (+st.snooze || 0) && ctAvail()""",
    """    return (+st.n || 0) >= 2 && !st.on && (+st.k || 0) < CT_ASK_MAX && Date.now() >= (+st.snooze || 0) && ctAvail()""")
p.write_text(s); print(p, 'popup-limits applied')
