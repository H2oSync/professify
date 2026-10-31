#!/usr/bin/env python3
"""Tate, 2026-10-30: "build in the enable notifications as a pop up or something, not that you have to go to settings."
The soft ask (SHEETS.pushAsk) only ever came at the end of onboarding, after watching a seat and after sending a chat,
so a student who signed up before it existed, or said "Not now" once, never saw it again without digging into Settings.
And once iOS has been told no, iOS never shows its dialog again, so Settings just said "Settings › TermChamp ›
Notifications" in words.

  1. One pop-up per app open, through a small queue (TC.popQueue(at, kind?) over POPS) that the "Connect contacts"
     pop-up can join: a launch (or back after 30+ min away) that is the 2nd+ launch or a day+ after sign-up, on a tab's
     top screen with no sheet or Champ open, shows "Turn on notifications?" while iOS hasn't asked yet. Each show snoozes
     it 7 days; it shows at most 3 times in all (onboarding's ask counts), then never.
  2. Notifications denied: "Notifications are off" with ONE button, Open Settings → window.location.href = 'app-settings:'
     (UIApplication.openSettingsURLString; Capacitor 8.5.2's WebViewDelegationHandler hands any top-level navigation off
     the app's own URL to UIApplication.shared.open). On an app open at most once every 30 days; right after watching a
     seat or unmuting a chat once per run; after sending a chat on the 30-day clock. Settings' "Notifications are off"
     line gets the same Open Settings button. Back from Settings with them on: registers and toasts "Notifications on".
  3. Web: PUSH.native() is false, so none of this shows (as before).

Target path argv[1] (default app/index.html). Exact-once replaces; asserts on a miss."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
assert 'TC.popQueue' not in s, 'already patched'

def one(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:120]); s = s.replace(a, b)

# ---- 1. the asks: copy, counters, the queue, the push kind, TC.pushAsk ----
one("""/* The soft ask, before iOS's own dialog — only while iOS hasn't asked yet, and never twice a week. */
const PUSH_ASK = {
  seat: ['Get a push when a seat opens?', 'We’ll tell you the moment a seat opens in a section you’re watching, so you can grab it first.'],
  chat: ['Know when they reply?', 'Get a notification when friends message you. You can mute any chat with its bell.'],
  onboarding: ['Turn on notifications?', 'Open seats, friend requests and messages. You choose exactly which in Settings.']
};
TC.pushAsk = async function (reason) {
  if (!PUSH.native() || !TC.ready) return;
  const st = await pushPerm(); if (st !== 'prompt' && st !== 'prompt-with-rationale') return;
  let until = 0; try { until = +localStorage.getItem(PUSH_SNOOZE_KEY) || 0; } catch (e) {}
  if (Date.now() < until || UI.sheet || UI.champ) return;
  UI.sheet = { type: 'pushAsk', reason }; render(true);
};
SHEETS.pushAsk = ({ reason }) => {
  const c = PUSH_ASK[reason] || PUSH_ASK.onboarding;
  return `<div style="text-align:center"><div class="okcircle" style="background:var(--blue-soft);color:var(--blue-t,var(--blue))">${ic('bell', 30, 2.2)}</div><h3>${c[0]}</h3><p class="muted b" style="font-size:14.5px;line-height:1.45;margin:6px 4px 16px">${c[1]}</p></div>
 <div style="display:grid;gap:8px"><button class="btn" data-a="pushAllow">Turn on notifications</button><button class="btn ghost" data-a="pushLater">Not now</button></div>`;
};""",
"""/* The soft ask, before iOS's own dialog — only while iOS hasn't asked yet, and never twice a week.
   (2026-10-30, Tate: "build in the enable notifications as a pop up or something, not that you have to go to settings")
   It also comes back on its own (the queue below), and once iOS has been told no — iOS never asks twice — it becomes
   "Notifications are off" with one button straight to TermChamp's page in iPhone Settings. */
const PUSH_ASK = {
  seat: ['Get a push when a seat opens?', 'We’ll tell you the moment a seat opens in a section you’re watching, so you can grab it first.'],
  chat: ['Know when they reply?', 'Get a notification when friends message you. You can mute any chat with its bell.'],
  onboarding: ['Turn on notifications?', 'Open seats, friend requests and messages. You choose exactly which in Settings.'],
  off: ['Notifications are off', 'Turn them on in Settings to hear about open seats and messages.']
};
PUSH_ASK.mute = PUSH_ASK.chat;
const PUSH_OPENS_KEY = 'tc_app_opens', PUSH_SHOWN_KEY = 'tc_push_ask_n', PUSH_OFF_KEY = 'tc_push_off_at';
const PUSH_ASK_MAX = 3, PUSH_OFF_EVERY = 30 * 864e5, POP_AWAY = 30 * 60000;
function lsNum(k) { try { return +localStorage.getItem(k) || 0; } catch (e) { return 0; } }
function lsSet(k, v) { try { localStorage.setItem(k, String(v)); } catch (e) {} }
/* ---- One pop-up per app open (2026-10-30) ----
   Pop-ups nobody tapped for (notifications now, "Connect contacts" next) queue here, so a student never gets two in a
   row. A kind adds { kind, due(at) → a truthy value when it wants to show (may be async), show(value, at) } to POPS;
   array order is priority. TC.popQueue(at, kind?) asks each kind in order (or only `kind`), shows the first that's due,
   and then nothing more until the next app open. at = 'onboarding' (setup just finished) or 'open' (a launch, or back
   after 30+ minutes away). Answers to a tap (watch a seat, send a chat) don't queue: they come right after the tap. */
const POPS = [], POPQ = { open: 0, shown: -1, busy: 0 };
function popClear(at) {
  if (!TC.ready || TC.phase !== 'ok' || UI.sheet || UI.champ) return false;
  if (at === 'onboarding') return true;
  const st = S.stack[S.tab] || [];
  return st.length === 1 && !Object.values(S.stack).some(x => x.some(e => e.s === 'onb'));   /* a tab's own screen, not mid-setup */
}
/* not the minute they signed up: a second launch, or an account a day old */
function popLaterOpen() { const c = TC.user && Date.parse(TC.user.created_at || ''); return lsNum(PUSH_OPENS_KEY) >= 2 || (c > 0 && Date.now() - c >= 864e5); }
TC.popQueue = async function (at, kind) {
  if (POPQ.busy || POPQ.shown === POPQ.open) return false;
  POPQ.busy = 1;
  try {
    for (const k of POPS) {
      if (kind && k.kind !== kind) continue;
      if (!popClear(at)) return false;
      let v = null; try { v = await k.due(at); } catch (e) {}
      if (v && popClear(at)) { POPQ.shown = POPQ.open; k.show(v, at); return k.kind; }
    }
    return false;
  } finally { POPQ.busy = 0; }
};
TC.pops = POPS;
function popAppOpened() { POPQ.open++; lsSet(PUSH_OPENS_KEY, lsNum(PUSH_OPENS_KEY) + 1); setTimeout(() => TC.popQueue('open'), 1200); }
function pushAskShow(reason) {
  if (reason === 'off') lsSet(PUSH_OFF_KEY, Date.now());
  else { lsSet(PUSH_SNOOZE_KEY, Date.now() + 7 * 864e5); if (reason === 'onboarding') lsSet(PUSH_SHOWN_KEY, lsNum(PUSH_SHOWN_KEY) + 1); }
  UI.sheet = { type: 'pushAsk', reason }; render(true);
}
POPS.push({ kind: 'push',
  due: async at => {
    if (!PUSH.native()) return null;
    if (at === 'open' && !popLaterOpen()) return null;
    const st = await pushPerm();
    if (st === 'prompt' || st === 'prompt-with-rationale') return Date.now() >= lsNum(PUSH_SNOOZE_KEY) && lsNum(PUSH_SHOWN_KEY) < PUSH_ASK_MAX ? 'onboarding' : null;
    if (st === 'denied') return Date.now() - lsNum(PUSH_OFF_KEY) >= PUSH_OFF_EVERY ? 'off' : null;
    return null;
  },
  show: reason => pushAskShow(reason) });
TC.pushAsk = async function (reason) {
  if (!PUSH.native() || !TC.ready) return;
  if (reason === 'onboarding') return TC.popQueue('onboarding');   /* end of setup: through the queue, so it and "Connect contacts" take turns */
  const st = await pushPerm();
  if (UI.sheet || UI.champ) return;
  if (st === 'denied') {
    /* right after a tap that needs them: watching a seat or unmuting a chat says so once a run; a sent message, once a month */
    if (reason === 'seat' || reason === 'mute' ? PUSH.offAsked : Date.now() - lsNum(PUSH_OFF_KEY) < PUSH_OFF_EVERY) return;
    PUSH.offAsked = 1; pushAskShow('off'); return;
  }
  if (st !== 'prompt' && st !== 'prompt-with-rationale') return;
  if (Date.now() < lsNum(PUSH_SNOOZE_KEY)) return;
  pushAskShow(reason);
};
SHEETS.pushAsk = ({ reason }) => {
  const off = reason === 'off', c = PUSH_ASK[reason] || PUSH_ASK.onboarding;
  return `<div style="text-align:center"><div class="okcircle" style="background:var(--blue-soft);color:var(--blue-t,var(--blue))">${ic(off ? 'bellOff' : 'bell', 30, 2.2)}</div><h3>${c[0]}</h3><p class="muted b" style="font-size:14.5px;line-height:1.45;margin:6px 4px 16px">${c[1]}</p></div>
 <div style="display:grid;gap:8px">${off ? '<button class="btn" data-a="pushOpenIOS">Open Settings</button>' : '<button class="btn" data-a="pushAllow">Turn on notifications</button>'}<button class="btn ghost" data-a="pushLater">Not now</button></div>`;
};""")

# ---- 2. Settings: the denied line is a button, not directions ----
one("""  else if (st === 'denied') top = '<div class="tc-err" style="margin-bottom:6px">Notifications are off for TermChamp. Turn them on in your iPhone’s Settings › TermChamp › Notifications.</div>';""",
"""  else if (st === 'denied') top = '<div class="tc-err" style="margin-bottom:6px">Notifications are off for TermChamp.</div><button class="btn soft" style="margin:2px 0 8px" data-a="pushOpenIOS">Open Settings</button>';""")

# ---- 3. app opens: a launch counts here; back after 30+ min away counts in the visibility listener ----
one("""TC.pushAfterLoad = async function () {
  pushLoadPrefs().then(() => render(true), () => {});""",
"""TC.pushAfterLoad = async function () {
  pushLoadPrefs().then(() => render(true), () => {});
  if (!PUSH.launched) { PUSH.launched = 1; popAppOpened(); }   /* the first load of this launch is an app open (a refresh isn't) */""")

one("""  document.addEventListener('visibilitychange', () => { if (document.visibilityState !== 'visible' || TC.phase !== 'ok') return;
    const was = PUSH.state; pushPerm().then(st => { if (st === 'granted') pushRegister(was !== 'granted' && was !== 'unknown'); if (st !== was) render(true); }); });""",
"""  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') { PUSH.hidAt = Date.now(); return; }
    if (document.visibilityState !== 'visible' || TC.phase !== 'ok') return;
    const away = PUSH.hidAt ? Date.now() - PUSH.hidAt : 0; PUSH.hidAt = 0;
    const was = PUSH.state; pushPerm().then(st => {
      if (st === 'granted') pushRegister(was !== 'granted' && was !== 'unknown');
      if (st === 'granted' && was === 'denied') { if (UI.sheet && UI.sheet.type === 'pushAsk') UI.sheet = null; render(true); toast('Notifications on'); }
      else if (st !== was) render(true);
      if (away >= POP_AWAY && TC.ready) popAppOpened();
    }); });""")

# ---- 4. actions: Open Settings; a "Don't Allow" starts the 30-day clock; "Not now" on the off variant just closes ----
one("""    try { const r = await p.requestPermissions(); PUSH.state = r.receive; if (r.receive === 'granted') { await pushRegister(true); toast('Notifications on. Choose which in Settings.'); } } catch (e) {}
    render(true);
  },
  pushLater: () => { try { localStorage.setItem(PUSH_SNOOZE_KEY, String(Date.now() + 7 * 864e5)); } catch (e) {} A.closeSheet(); },""",
"""    try { const r = await p.requestPermissions(); PUSH.state = r.receive; if (r.receive === 'granted') { await pushRegister(true); toast('Notifications on. Choose which in Settings.'); } else if (r.receive === 'denied') lsSet(PUSH_OFF_KEY, Date.now()); } catch (e) {}
    render(true);
  },
  pushLater: () => { if (!(UI.sheet && UI.sheet.reason === 'off')) lsSet(PUSH_SNOOZE_KEY, Date.now() + 7 * 864e5); A.closeSheet(); },
  /* TermChamp's own page in iPhone Settings, one tap. 'app-settings:' is UIApplication.openSettingsURLString; Capacitor's
     WebViewDelegationHandler (8.5.2) sends a top-level navigation that isn't the app's own URL to UIApplication.shared.open
     and cancels it in the web view. Coming back, the visibility listener above re-checks and registers. */
  pushOpenIOS: () => {
    if (UI.sheet && UI.sheet.type === 'pushAsk') { UI.sheet = null; render(true); }
    PUSH.toSettingsAt = Date.now();
    try { window.location.href = 'app-settings:'; } catch (e) {}
  },""")

# ---- 5. unmuting a chat needs notifications too ----
one("""    toast(was ? 'Unmuted. You’ll get notifications from this chat.' : 'Muted. No notifications from this chat.');
  }""",
"""    toast(was ? 'Unmuted. You’ll get notifications from this chat.' : 'Muted. No notifications from this chat.');
    if (was) TC.pushAsk('mute');
  }""")

p.write_text(s); print(p, 'push pop-ups: patched')
