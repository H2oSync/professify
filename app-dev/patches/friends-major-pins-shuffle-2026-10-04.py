#!/usr/bin/env python3
"""A friend's major, pinned stories, and a shuffling pull-to-refresh (Tate, 2026-10-04).

1. "i should also be able to see friends majors and concentrations. in a well designed way":
   a friend's page shows their major in a teal pill with the cap icon, and under it
   "<concentration> concentration · <year>". The friends read asks for class_standing and
   concentration too; `concentration` is not granted to `authenticated` until
   sql/professify-concentration-visible.sql runs, so a 42501 falls back to the read without it
   (and isn't tried again this session). No major and no year → nothing is drawn.
2. "lets also make it so you can pin 3 friends on stories": hold a story (or tap the pin in a story
   or on a friend's page) to pin it. Pinned friends go first, in the order you pinned them, with a
   small blue pin on the ring. Three at most; a fourth is refused by name. Kept on this phone, per
   account (like Recent searches); nothing is sent to the server.
3. "swipe down on the homepage ... refreshes and shuffles friends schedules ... always random and not
   the same schedules displayed again ... the refresh little thing is in between the feed and the
   stories and then smoothly displays the refreshed schedules": the feed's order is random on every
   open; each pull reloads, then reshuffles so the cards you saw at the top (two of them from four
   friends up, one from two or three) are not at the top again. The spinner opens a gap between the
   stories and the feed as you pull; the old feed fades, the gap closes and the new cards rise in.
   Reduced motion: no fade or rise.

Applies after me-no-stat-tiles-2026-10-04.py.
Usage: python3 friends-major-pins-shuffle-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function feedOrder()' in s: sys.exit('already patched')
R = [
 # icon
 (""" grad:'<path d="M2.5 9.5 12 5l9.5 4.5L12 14z"/><path d="M6.5 11.5V16c1.5 1.3 3.3 2 5.5 2s4-.7 5.5-2v-4.5"/>',""",
  """ grad:'<path d="M2.5 9.5 12 5l9.5 4.5L12 14z"/><path d="M6.5 11.5V16c1.5 1.3 3.3 2 5.5 2s4-.7 5.5-2v-4.5"/>',
 pin:'<path d="M12 16.5V21"/><path d="M8.5 3.5h7M9.5 3.5v5.5L6.5 12.5v3.5h11v-3.5L14.5 9V3.5"/>',"""),
 # 1. friends read: year and concentration
 ("""    for (const sel of ['id,display_name,username,avatar_url,major', 'id,display_name,username,avatar_url']) {
      const r = await sb.from('profiles').select(sel).in('id', other);
      if (!r.error) { profs = r.data; break; }
      if (!schemaGap(r.error)) break;
    }
    (profs || []).forEach(p => { PEOPLE[p.id] = Object.assign(PEOPLE[p.id] || {}, personFrom(p), { major: p.major || '' });""",
  """    /* `concentration` is readable only once sql/professify-concentration-visible.sql has run; before
       that PostgREST refuses the whole read with 42501, so drop it (for this session) and read again. */
    let withConc = false;
    for (const sel of ['id,display_name,username,avatar_url,major,class_standing,concentration', 'id,display_name,username,avatar_url,major,class_standing', 'id,display_name,username,avatar_url,major', 'id,display_name,username,avatar_url']) {
      if (TC.noConc && Date.now() - TC.noConc < 600000 && /concentration/.test(sel)) continue;   /* tried again after 10 minutes, so running the SQL shows up without a restart */
      const r = await sb.from('profiles').select(sel).in('id', other);
      if (!r.error) { profs = r.data; withConc = /concentration/.test(sel); break; }
      if (String(r.error.code) === '42501' && /concentration/.test(sel)) { TC.noConc = Date.now(); continue; }
      if (!schemaGap(r.error)) break;
    }
    (profs || []).forEach(p => { PEOPLE[p.id] = Object.assign(PEOPLE[p.id] || {}, personFrom(p), { major: p.major || '', standing: p.class_standing || '', conc: withConc ? p.concentration || '' : '' });"""),
 # 1. friend page: major block, and a pin beside Message
 ("""${st && st.free !== null ? `<span style="color:${st.c || 'var(--muted)'}">${esc(st.t)}</span>` : ''}</div>` : ''}
  <div class="row" style="justify-content:center;margin-top:14px;gap:10px">${isF ? `<button class="pbtn pink" style="height:42px;width:200px" data-a="openChatWith" data-x="${id}">Message</button>`""",
  """${st && st.free !== null ? `<span style="color:${st.c || 'var(--muted)'}">${esc(st.t)}</span>` : ''}</div>` : ''}${isF ? majorBlock(p) : ''}
  <div class="row" style="justify-content:center;margin-top:14px;gap:10px">${isF ? `<button class="pbtn pink" style="height:42px;width:200px" data-a="openChatWith" data-x="${id}">Message</button>${pinBtn(id, 'fpin')}`"""),
 # 2. story order: pins first
 ("""  return UI.storyOrder;
}
/* A friend's day: what a story opens. */""",
  """  const pins = pinsGet();
  return pins.length ? pins.concat(UI.storyOrder.filter(id => pins.indexOf(id) < 0)) : UI.storyOrder;
}
/* ---- pinned stories (Tate, 2026-10-04: "pin 3 friends on stories") ----
   Up to three, first in the row in the order pinned. Kept on this phone per account; never sent. */
const PIN_MAX = 3;
function pinKey() { return 'tc-story-pins:' + (TC.user ? TC.user.id : ''); }
function pinsSaved() { let a = []; try { a = JSON.parse(localStorage.getItem(pinKey()) || '[]'); } catch (e) {} return Array.isArray(a) ? a.filter(x => typeof x === 'string') : []; }
/* what shows: saved pins that are friends right now (a friend list still loading drops nobody) */
function pinsGet() { return pinsSaved().filter(id => TC.friends.indexOf(id) >= 0).slice(0, PIN_MAX); }
function pinsSet(a) { try { localStorage.setItem(pinKey(), JSON.stringify(a)); return true; } catch (e) { return false; } }
function orList(a) { return a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' or ' + a[a.length - 1]; }
function togglePin(id) {
  if (!id || TC.friends.indexOf(id) < 0) return;
  const a = pinsGet(), all = pinsSaved(), nm = PEOPLE[id].short, fe = document.activeElement, refocus = !!(fe && fe.dataset && fe.dataset.a === 'togglePin');
  if (a.indexOf(id) >= 0) { if (!pinsSet(all.filter(x => x !== id))) return toast('Couldn’t save that on this phone'); toast('Unpinned ' + nm); }
  else if (a.length >= PIN_MAX) return toast('3 pinned already — unpin ' + orList(a.map(x => PEOPLE[x].short)) + ' first');
  else { if (!pinsSet(all.filter(x => TC.friends.indexOf(x) < 0 || a.indexOf(x) >= 0).concat(id))) return toast('Couldn’t save that on this phone'); toast('Pinned ' + nm + ' to the front'); }
  render(true);
  if (refocus) { const b = [...document.querySelectorAll('[data-a="togglePin"]')].find(x => x.dataset.x === id && x.offsetParent); if (b) b.focus(); }
}
function pinBtn(id, cls) {
  const on = pinsGet().indexOf(id) >= 0, nm = esc(PEOPLE[id] ? PEOPLE[id].short : '');
  return `<button class="pinbtn ${cls}${on ? ' on' : ''}" data-a="togglePin" data-x="${esc(id)}" aria-pressed="${on}" aria-label="Pin ${nm} to the front of your stories">${ic('pin', cls === 'stpin' ? 17 : 19, 2.2)}</button>`;
}
/* Hold a story to pin or unpin it. A hold is never also a tap; the next tap is. */
const SLP = { t: null, x: 0, y: 0, fired: false };
(function () {
  const start = (el, x, y) => { clearTimeout(SLP.t); SLP.fired = false; SLP.x = x; SLP.y = y; SLP.t = setTimeout(() => { SLP.t = null; SLP.fired = true; try { if (navigator.vibrate) navigator.vibrate(12); } catch (e) {} togglePin(el.dataset.x); }, 500); };
  const moved = (x, y) => { if (SLP.t && Math.hypot(x - SLP.x, y - SLP.y) > 8) stop(); };
  const stop = () => { clearTimeout(SLP.t); SLP.t = null; };
  const story = t => t && t.closest ? t.closest('.stories .story[data-a="story"]') : null;
  /* touchend goes to the story the finger went down on, even after a re-render has detached it — listen there too */
  document.addEventListener('touchstart', e => { const el = story(e.target); if (el && e.touches.length === 1) { start(el, e.touches[0].clientX, e.touches[0].clientY); el.addEventListener('touchend', done, { once: true, passive: true }); } else stop(); }, { passive: true });
  document.addEventListener('touchmove', e => { if (e.touches.length) moved(e.touches[0].clientX, e.touches[0].clientY); }, { passive: true });
  /* the click a hold leaves behind comes right after letting go, or never (Android, keyboard) */
  const done = () => { stop(); if (SLP.fired) setTimeout(() => { SLP.fired = false; }, 400); };
  document.addEventListener('touchend', done, { passive: true }); document.addEventListener('touchcancel', done, { passive: true });
  document.addEventListener('mousedown', e => { const el = story(e.target); if (el && e.button === 0) start(el, e.clientX, e.clientY); });
  document.addEventListener('mousemove', e => moved(e.clientX, e.clientY)); document.addEventListener('mouseup', done);
  document.addEventListener('contextmenu', e => { if (story(e.target)) e.preventDefault(); });
  document.addEventListener('click', e => { if (SLP.fired && e.target.closest && e.target.closest('.story')) { SLP.fired = false; e.stopPropagation(); e.preventDefault(); } }, true);
})();
/* ---- a friend's major (Tate, 2026-10-04) ---- */
function majorBlock(p) {
  const c = p.conc && p.conc !== 'General / Open' ? p.conc + (/concentration/i.test(p.conc) ? '' : ' concentration') : '';
  const sub = [c, p.standing].filter(Boolean).join(' · ');
  if (!p.major && !sub) return '';
  return `<div class="fmaj">${p.major ? `<span class="fmaj-pill">${ic('grad', 17, 2.2)}<span>${esc(p.major)}</span></span>` : ''}${sub ? `<div class="fmaj-sub">${esc(sub)}</div>` : ''}</div>`;
}
/* ---- Home's feed order (Tate, 2026-10-04) ----
   Random on every open. Each pull shuffles again, and the cards that were at the top (two from four
   friends up, one from two or three) are never at the top again — "not the same schedules". */
function shuffleArr(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
function reshuffle(prev, ids) {
  const k = Math.min(2, Math.floor(ids.length / 2)), top = (prev || []).filter(id => ids.indexOf(id) >= 0).slice(0, k);
  if (!k || !top.length) return shuffleArr(ids);
  const pool = shuffleArr(ids.filter(id => top.indexOf(id) < 0));
  return pool.slice(0, k).concat(shuffleArr(pool.slice(k).concat(top)));
}
function feedOrder() {
  const f = TC.friends, o = UI.feedOrder;
  if (!o || o.length !== f.length || o.some(id => f.indexOf(id) < 0)) UI.feedOrder = shuffleArr(f);
  return UI.feedOrder;
}
/* the rise-in runs once: whichever render draws it first uses it up */
function feedAnimDone() { if (!UI.feedIn) return; UI.feedIn = false; clearTimeout(feedAnimDone.t); feedAnimDone.t = setTimeout(() => { const f = document.querySelector('.hfeed.fin'); if (f) f.classList.remove('fin'); }, 900); }
function hptr() { return `<div class="hptr${PTR.busy ? ' spin' : ''}" id="hptr" style="height:${PTR.busy || PTR.closing ? 56 : 0}px" aria-hidden="true"><span class="tc-spin"></span></div>`; }
/* A friend's day: what a story opens. */"""),
 # 2. pin in a story's sheet
 ("""<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="flabel" style="margin:16px 0 6px">${esc(DAYL[CLOCK.day] || 'Today')} · today</div>""",
  """<span class="row" style="gap:8px;flex:none">${pinBtn(id, 'stpin')}<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></span></div>
 <div class="flabel" style="margin:16px 0 6px">${esc(DAYL[CLOCK.day] || 'Today')} · today</div>"""),
 # 2. Home stories: pinned badge
 ("""  const stories = storyOrder().map(id => { const p = PEOPLE[id], st = status(id); return `<button class="story" data-a="story" data-x="${esc(id)}">""",
  """  const pins = pinsGet(), stories = storyOrder().map(id => { const p = PEOPLE[id], st = status(id), pin = pins.indexOf(id) >= 0; return `<button class="story${pin ? ' pinned' : ''}" data-a="story" data-x="${esc(id)}"${pin ? ` aria-label="${esc(p.short)}, pinned"` : ''}>"""),
 ("""</span><span class="nm">${esc(p.short)}</span></button>`; }).join('');""",
  """${pin ? `<i class="pinbadge" aria-hidden="true">${ic('pin', 12, 2.6)}</i>` : ''}</span><span class="nm">${esc(p.short)}</span></button>`; }).join('');"""),
 # 3. Home feed: shuffled order, the spinner between stories and feed
 ("  const feed = TC.friends.length ? TC.friends.map(homeWeekCard).join('')",
  "  const fin = UI.feedIn; feedAnimDone();\n  const feed = TC.friends.length ? feedOrder().map(homeWeekCard).join('')"),
 # a load that finished (homeRefresh tells a finished refresh from a failed or timed-out one)
 ("  UI.storyOrder = null; TC.ready = true; render(true);\n  startRealtime();", "  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);\n  startRealtime();"),
 (""" <div class="hfeed">${feed}</div>""",
  """ ${hptr()}<div class="hfeed${UI.feedOut ? ' fout' : fin ? ' fin' : ''}">${feed}</div>"""),
 # 3. pull-to-refresh: the gap opens under the stories
 ("""function ptrEl() { let el = document.getElementById('ptr'); if (!el) { el = document.createElement('div'); el.id = 'ptr'; el.setAttribute('aria-hidden', 'true'); el.innerHTML = '<span class="tc-spin"></span>'; (document.querySelector('.phone') || document.body).appendChild(el); } return el; }""",
  """/* 2026-10-04: the spinner lives between the stories and the feed (#hptr, drawn by SCREENS.home);
   pulling opens that gap, and the feed slides down with it. */
function ptrEl() { return document.getElementById('hptr') || document.createElement('div'); }
function ptrClose() { const el = ptrEl(), sp = el.firstElementChild; el.classList.remove('drag', 'armed', 'spin'); el.style.height = '0px'; if (sp) sp.style.opacity = ''; }"""),
 ("""  const el = ptrEl(), d = Math.min(PTR.dy, 120); el.style.opacity = String(Math.min(1, d / 70)); el.style.transform = `translate(-50%,${Math.round(d * 0.6) - 40}px)`; el.classList.toggle('armed', PTR.dy >= 70);""",
  """  const el = ptrEl(), d = Math.min(PTR.dy, 140), sp = el.firstElementChild; el.classList.add('drag'); el.style.height = Math.round(d * 0.5) + 'px'; if (sp) sp.style.opacity = String(Math.min(1, d / 70)); el.classList.toggle('armed', PTR.dy >= 70);"""),
 ("""  if (go) homeRefresh(); else { const el = ptrEl(); el.style.opacity = '0'; el.style.transform = ''; el.classList.remove('armed'); }""",
  """  if (go) homeRefresh(); else ptrClose();"""),
 ("""  if (PTR.busy) return; PTR.busy = true; const el = ptrEl(); el.classList.add('spin'); el.style.opacity = '1'; el.style.transform = 'translate(-50%,20px)';
  try { await Promise.race([TC.load(), new Promise(r => setTimeout(r, 15000))]); } catch (e) {}
  UI.storyOrder = null; PTR.busy = false; el.classList.remove('spin', 'armed'); el.style.opacity = '0'; el.style.transform = ''; render(true);
}""",
  """  if (PTR.busy) return; PTR.busy = true; const el = ptrEl(), sp = el.firstElementChild; el.classList.remove('drag'); el.classList.add('spin'); el.style.height = '56px'; if (sp) sp.style.opacity = '';
  const shown = (UI.feedOrder || []).slice(), t0 = Date.now();
  try { await Promise.race([TC.load(), new Promise(r => setTimeout(r, 15000))]); } catch (e) {}
  let still = false;
  try {
    const hold = 450 - (Date.now() - t0); if (hold > 0) await new Promise(r => setTimeout(r, hold));   /* long enough to see it turn */
    /* Only a refresh that worked reshuffles; one that didn't says so and keeps what you were looking at. */
    const loaded = TC.loadDone >= t0, ok = loaded && !TC.err.friends && !TC.err.friendSecs;
    if (!loaded) toast('Couldn’t refresh — check your connection');
    else if (!ok) toast(TC.err.friends ? 'Couldn’t load your friends — pull down to try again' : 'Couldn’t load your friends’ classes — pull down to try again');
    UI.storyOrder = null;
    if (ok) {
      UI.feedOrder = reshuffle(shown, TC.friends);
      still = !(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
      const fd = document.querySelector('.hfeed');
      if (still && fd && ptrOn()) { UI.feedOut = true; fd.classList.add('fout'); await new Promise(r => setTimeout(r, 170)); }
    }
  } catch (e) { still = false; }
  finally { PTR.busy = false; PTR.closing = true; UI.feedOut = false; UI.feedIn = still; }
  render(true);
  requestAnimationFrame(() => requestAnimationFrame(() => { PTR.closing = false; ptrClose(); }));
}"""),
 # the toast is read out (a refused fourth pin says why)
 ('<div id="toast"></div>', '<div id="toast" role="status" aria-live="polite"></div>'),
 # actions
 ("""  story: id => { if (id && TC.friends.indexOf(id) >= 0) {""",
  """  togglePin: id => togglePin(id),
  story: id => { if (id && TC.friends.indexOf(id) >= 0) {"""),
 # CSS
 ("""#ptr .tc-spin{margin:0;width:20px;height:20px;animation-play-state:paused}
#ptr.armed .tc-spin,#ptr.spin .tc-spin{animation-play-state:running}""",
  """.hptr{height:0;overflow:hidden;display:grid;place-items:center;transition:height .3s cubic-bezier(.2,.8,.2,1)}
.hptr.drag{transition:none}
.hptr .tc-spin{margin:0;width:24px;height:24px;opacity:0;transition:opacity .15s;animation-play-state:paused}
.hptr.armed .tc-spin,.hptr.spin .tc-spin{opacity:1;animation-play-state:running}
.hfeed.fout{opacity:0;transform:translateY(6px);transition:opacity .17s ease,transform .17s ease}
.hfeed.fin .fcard{animation:fcIn .42s cubic-bezier(.2,.8,.2,1) both}
.hfeed.fin .fcard:nth-child(2){animation-delay:.05s}.hfeed.fin .fcard:nth-child(3){animation-delay:.1s}.hfeed.fin .fcard:nth-child(n+4){animation-delay:.15s}
@keyframes fcIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.hptr{transition:none}.hfeed.fout{transition:none}.hfeed.fin .fcard{animation:none}}
.story{-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}
.story .ring{position:relative}
.pinbadge{position:absolute;right:0;bottom:0;width:22px;height:22px;border-radius:50%;background:var(--blue);color:#fff;display:grid;place-items:center;box-shadow:0 0 0 2.5px var(--bg)}
.pinbtn{width:42px;height:42px;border-radius:50%;display:grid;place-items:center;background:#fff;color:var(--ink3);box-shadow:0 1px 3px rgba(15,23,42,.14);flex:none}
.pinbtn.stpin{width:34px;height:34px;background:var(--bg);box-shadow:none}
.pinbtn.on{background:var(--blue);color:#fff}
.fmaj{display:flex;flex-direction:column;align-items:center;gap:5px;margin-top:10px}
.fmaj-pill{display:inline-flex;align-items:center;gap:7px;max-width:100%;padding:7px 15px 7px 12px;border-radius:999px;background:var(--teal-soft);color:var(--teal);font-weight:900;font-size:14.5px;line-height:1.25;text-align:left}
.fmaj-pill svg{flex:none}
.fmaj-sub{font-size:13.5px;font-weight:800;color:var(--ink3);max-width:320px;line-height:1.3}"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
# the old floating spinner's own rule
import re
old = re.findall(r'^#ptr\{[^\n]*\}\n', s, re.M)
if len(old) != 1: sys.exit(f'#ptr rule matched {len(old)}x')
s = s.replace(old[0], '')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
