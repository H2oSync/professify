#!/usr/bin/env python3
"""Stories are about today and who's free; the feed stays the weeks (Tate, 2026-09-30).

1. "Friends who are most free right now go furthest left":
   free now (longest free stretch first) → free soonest (about to start a class; soonest out of it
   first) → in class (getting out soonest first) → no classes added. Ties keep one fixed order
   (name, then id), so the row is predictable. The order is worked out when Home is opened (app
   start, tapping the Home tab, a refresh) and then HELD while you look at it: the rings keep
   updating every minute, the circles don't move under your thumb.
2. "swipe down on the homepage like instagram and it refreshes. Everything": pull down from the top
   of Home past 70px and let go — everything reloads (TC.load: profile, your classes, friends,
   plans, watches, reviews, chats) and the stories re-sort. Works with a finger on the phone and a
   mouse drag in the Desktop preview; a drag never also counts as a tap.
3. "when you click on a friends story it shouldnt bring you to their schedule on the feed. it
   should show the current persons day schedule, times of classes for the day, teacher and ratings
   and friends in the class with them": a story opens that friend's DAY — today's classes in time
   order with the time, the professor and their rating (or "No ratings yet"), and who else you know
   is in that section (you included) — with the free stretches between classes, "Now" on the one
   they're in, and ‹ › to step through the stories in the same order as the row.
   Nothing is invented: an online section is listed as online, a class with no set time isn't put
   at an hour, and a friend with no classes added says so.
(The feed is untouched: it is still everyone's current week, and becomes plans after Oct 5.)

Applies after share-week-2026-09-30.py.
Usage: python3 stories-now-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'SHEETS.story = ' in s: sys.exit('already patched')

JS = r"""
/* ================= stories: today, most free first (Tate, 2026-09-30) ================= */
function todaySecs(id) { return personSecs(id).filter(x => !x.async && x.s != null && x.e != null && x.days.includes(CLOCK.day)).sort((a, b) => a.s - b.s); }
/* [group, key]: 0 free now (longest free stretch first); 1 busy — in a class, or about to start one —
   by when they're next free, soonest first (a class straight after another counts as the same busy
   stretch); 2 no classes added. */
function storyRank(id) {
  const st = status(id), now = CLOCK.min, today = todaySecs(id);
  if (st.free === null) return [2, 0];
  const inc = today.find(x => x.s <= now && now < x.e), nx = today.find(x => x.s > now);
  if (st.free && !inc) return [0, -(nx ? nx.s - now : 1e6)];
  let t = inc ? inc.e : nx ? nx.e : now;
  today.forEach(x => { if (x.e > t && x.s <= t + 10) t = x.e; });
  return [1, t];
}
function storyOrder() {
  const o = UI.storyOrder, f = TC.friends;
  if (!o || o.length !== f.length || o.some(id => f.indexOf(id) < 0)) {
    const rk = {}; f.forEach(id => { rk[id] = storyRank(id); });
    UI.storyOrder = f.slice().sort((a, b) => (rk[a][0] - rk[b][0]) || (rk[a][1] - rk[b][1]) || PEOPLE[a].name.localeCompare(PEOPLE[b].name) || (a < b ? -1 : a > b ? 1 : 0));
  }
  return UI.storyOrder;
}
/* A friend's day: what a story opens. */
SHEETS.story = ({ id }) => {
  const p = PEOPLE[id]; if (!p || TC.friends.indexOf(id) < 0) return '';
  const st = status(id), now = CLOCK.min, today = todaySecs(id), mine = personSecs('me');
  /* the same classes Home's Anytime tray shows: no time slot (online, time not posted) or no section yet */
  const all = personSecs(id), anyC = [...new Set(all.filter(x => x.async || x.s == null || x.e == null).map(x => x.code).concat((p.unplaced || []).filter(c => !all.some(x => x.code === c))))], ntimed = all.length - all.filter(x => x.async || x.s == null || x.e == null).length;
  const ord = storyOrder(), i = ord.indexOf(id), prev = ord[i - 1], next = ord[i + 1];
  const rating = pk => { const r = ratingOf(pk); return r != null ? `${starI(13, rateTone(r).star)}<span class="rt-${rateTone(r).k}" style="color:${rateTone(r).ink}">${r.toFixed(1)}</span><span class="muted" style="font-weight:700">&nbsp;· ${nRatings(PROFS[pk].count)}</span>` : '<span class="muted" style="font-weight:700">No ratings yet</span>'; };
  const withThem = x => { const w = friendsInSec(x.id).filter(f => f !== id), me = mine.some(y => y.id === x.id); const nm = (me ? ['You'] : []).concat(w.map(f => PEOPLE[f].short)); return nm.length ? `<div class="stwith">${avStack((me ? ['me'] : []).concat(w), 22)}<span>With them: ${esc(nm.slice(0, 3).join(', ') + (nm.length > 3 ? ' +' + (nm.length - 3) : ''))}</span></div>` : ''; };
  let rows = '', last = null;
  today.forEach(x => {
    const from = last == null ? null : last; if (from != null && x.s - from >= 30) rows += `<div class="stfree">Free ${hs(from)}–${hs(x.s)}</div>`;
    const isNow = x.s <= now && now < x.e, past = x.e <= now;
    rows += `<div class="strow${isNow ? ' now' : ''}${past ? ' past' : ''}"><div class="sttm">${hs(x.s)}<small>${hs(x.e)}</small></div><div class="grow" style="min-width:0">
  <button class="stcode" data-a="openClass" data-x="${esc(x.code)}"><b>${esc(x.code)}</b>${(t => t && t !== x.code ? ` <span>${esc(t)}</span>` : '')(course(x.code).title)}</button>${isNow ? '<span class="stnow">Now</span>' : ''}
  ${x.prof && PROFS[x.prof] ? `<button class="stprof" data-a="openProf" data-x="${esc(x.prof)}"><span class="nm">${esc(profName(x.prof))}</span>${rating(x.prof)}</button>` : '<div class="stprof muted">Instructor not assigned</div>'}
  ${withThem(x)}</div></div>`;
    last = Math.max(last == null ? 0 : last, x.e);
  });
  const body = !ntimed && !anyC.length ? `<div class="empty"><b>${esc(p.short)} hasn’t added classes</b></div>`
    : today.length ? rows
    : !ntimed ? `<div class="empty"><b>No set class times</b>${esc(p.short)}’s classes are all anytime.</div>`
    : `<div class="empty"><b>No classes today</b>${esc(p.short)} is free all ${esc(DAYL[CLOCK.day] || 'day')}.</div>`;
  return `<div class="row sb"><div class="row" style="gap:12px;min-width:0"><span class="ringav" style="--rc:${st.c || 'transparent'}">${pav(id, 52, 18)}</span><div style="min-width:0"><div style="font-weight:900;font-size:19px">${esc(p.name)}</div>${st.free !== null || st.t ? `<div class="b" style="font-size:13.5px;color:${st.c || 'var(--muted)'}">● ${esc(st.t)}</div>` : ''}</div></div><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="flabel" style="margin:16px 0 6px">${esc(DAYL[CLOCK.day] || 'Today')} · today</div>
 ${body}
 ${anyC.length ? `<div class="stonl">Anytime: ${anyC.map(c => esc(c)).join(', ')}</div>` : ''}
 <div class="stnav"><button class="iconbtn" data-a="story" data-x="${esc(prev || '')}" ${prev ? '' : 'disabled'} aria-label="${prev ? esc('Previous: ' + PEOPLE[prev].short) : 'No previous story'}">${ic('chevL', 20, 2.4)}</button>
  <button class="btn soft" data-a="openChatWith" data-x="${esc(id)}">Message</button><button class="btn soft" data-a="openFriend" data-x="${esc(id)}">Full week</button>
  <button class="iconbtn" data-a="story" data-x="${esc(next || '')}" ${next ? '' : 'disabled'} aria-label="${next ? esc('Next: ' + PEOPLE[next].short) : 'No next story'}">${ic('chevR', 20, 2.4)}</button></div>`;
};
/* Pull down on Home to refresh everything (Tate, 2026-09-30). */
const PTR = { y0: null, dy: 0, busy: false, swallow: false };
function ptrEl() { let el = document.getElementById('ptr'); if (!el) { el = document.createElement('div'); el.id = 'ptr'; el.setAttribute('aria-hidden', 'true'); el.innerHTML = '<span class="tc-spin"></span>'; (document.querySelector('.phone') || document.body).appendChild(el); } return el; }
function ptrOn() { const e = cur(); return TC.phase === 'ok' && S.tab === 'home' && !!e && e.s === 'home' && !UI.sheet && !UI.champ; }
function ptrStart(y) { const sc = document.getElementById('scroll'); PTR.swallow = false; PTR.y0 = (!PTR.busy && ptrOn() && sc && sc.scrollTop <= 0) ? y : null; PTR.dy = 0; }
function ptrMove(y) {
  if (PTR.y0 == null) return; PTR.dy = Math.max(0, y - PTR.y0);
  const el = ptrEl(), d = Math.min(PTR.dy, 120); el.style.opacity = String(Math.min(1, d / 70)); el.style.transform = `translate(-50%,${Math.round(d * 0.6) - 40}px)`; el.classList.toggle('armed', PTR.dy >= 70);
}
/* A mouse drag is followed by a click on whatever it started on; swallow that one. A moved touch
   never makes a click, so it must not arm this — it would eat the next real tap. */
function ptrEnd(mouse) {
  if (PTR.y0 == null) return; const go = PTR.dy >= 70; if (mouse === true && PTR.dy >= 10) { PTR.swallow = true; setTimeout(() => { PTR.swallow = false; }, 60); } PTR.y0 = null;
  if (go) homeRefresh(); else { const el = ptrEl(); el.style.opacity = '0'; el.style.transform = ''; el.classList.remove('armed'); }
}
async function homeRefresh() {
  if (PTR.busy) return; PTR.busy = true; const el = ptrEl(); el.classList.add('spin'); el.style.opacity = '1'; el.style.transform = 'translate(-50%,20px)';
  try { await Promise.race([TC.load(), new Promise(r => setTimeout(r, 15000))]); } catch (e) {}
  UI.storyOrder = null; PTR.busy = false; el.classList.remove('spin', 'armed'); el.style.opacity = '0'; el.style.transform = ''; render(true);
}
(function () {
  const sc = document.getElementById('scroll'); if (!sc) return;
  sc.addEventListener('touchstart', e => { if (e.touches.length === 1) ptrStart(e.touches[0].clientY); }, { passive: true });
  sc.addEventListener('touchmove', e => { if (e.touches.length === 1) ptrMove(e.touches[0].clientY); }, { passive: true });
  sc.addEventListener('touchend', () => ptrEnd(false), { passive: true }); sc.addEventListener('touchcancel', () => { PTR.dy = 0; ptrEnd(false); }, { passive: true });
  sc.addEventListener('mousedown', e => { if (e.button === 0) ptrStart(e.clientY); });
  document.addEventListener('mousemove', e => { if (PTR.y0 != null && (e.buttons & 1)) ptrMove(e.clientY); });
  document.addEventListener('mouseup', () => ptrEnd(true));
  /* a drag is never also a tap */
  document.addEventListener('click', e => { if (PTR.swallow) { PTR.swallow = false; e.stopPropagation(); e.preventDefault(); } }, true);
})();
"""

R = [
 # stories: most free first, and a tap opens their day
 ("  const stories = TC.friends.map(id => { const p = PEOPLE[id], st = status(id); return `<button class=\"story\" data-a=\"homeFriend\" data-x=\"${esc(id)}\">",
  "  const stories = storyOrder().map(id => { const p = PEOPLE[id], st = status(id); return `<button class=\"story\" data-a=\"story\" data-x=\"${esc(id)}\">"),
 ("  homeFriend: id => {\n    const el = document.getElementById('hf-' + id); if (!el) return;\n    const calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;\n    el.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' });\n    el.classList.remove('hf-flash'); void el.offsetWidth; el.classList.add('hf-flash');\n  },\n",
  "  story: id => { if (id && TC.friends.indexOf(id) >= 0) { UI.sheet = { type: 'story', id }; render(true); const b = document.querySelector('#sheet .sbody'); if (b) b.scrollTop = 0; } },\n"),
 # re-sort when Home is opened (tab), and once everything has loaded (start-up, refresh)
 ("function setTab(t) { if (t !== 'schedule') UI.plFor = null;",
  "function setTab(t) { if (t === 'home') UI.storyOrder = null; if (t !== 'schedule') UI.plFor = null;"),
 ("  loadSuggestions(); loadRateList(); loadFriendPlans();\n  TC.ready = true; render(true);",
  "  loadSuggestions(); loadRateList(); loadFriendPlans();\n  UI.storyOrder = null; TC.ready = true; render(true);"),
 # a refresh (pull, or coming back to the app) keeps your place and never throws you out of the app
 ("  TC.phase = 'ok'; onbResume(); render();\n  await Promise.all([loadMine(),",
  "  TC.phase = 'ok'; onbResume(); render(!!TC.ready);\n  await Promise.all([loadMine(),"),
 ("  TC.profile = p.data || null;\n",
  "  /* a refresh that fails keeps the profile you have (nulling it broke every later profile edit) */\n  if (p.error && TC.ready) { toast('Couldn’t refresh — check your connection'); return; }\n  TC.profile = p.data || null;\n"),
 # the module, after the other sheets' helpers
 ("const SHEETS = {};\n", "const SHEETS = {};\n" + JS.lstrip('\n')),
 # styles
 (".ringav{border-radius:50%;padding:3px;box-shadow:inset 0 0 0 2.5px var(--rc,transparent);flex:none}\n",
  ".ringav{border-radius:50%;padding:3px;box-shadow:inset 0 0 0 2.5px var(--rc,transparent);flex:none}\n"
  "/* a friend's day (stories, 2026-09-30) */\n"
  ".strow{display:flex;gap:12px;padding:12px 0;border-top:1px solid var(--line)}\n"
  ".strow.past{opacity:.55}\n"
  ".strow.now .sttm{color:var(--blue)}\n"
  ".sttm{flex:none;width:52px;font-weight:900;font-size:15px;color:var(--ink);line-height:1.15}\n"
  ".sttm small{display:block;font-size:12.5px;font-weight:800;color:var(--muted)}\n"
  ".stcode{display:block;text-align:left;font-size:15px;line-height:1.3;color:var(--ink);min-height:24px}\n"
  ".stcode span{font-weight:700;color:var(--ink3)}\n"
  ".stnow{display:inline-block;margin-top:3px;font-size:11.5px;font-weight:900;color:#fff;background:var(--blue);padding:2px 8px;border-radius:10px}\n"
  ".stprof{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin-top:4px;font-size:13.5px;font-weight:800;text-align:left;min-height:26px}\n"
  ".stprof .nm{color:var(--ink3);margin-right:4px}\n"
  ".stwith{display:flex;align-items:center;gap:8px;margin-top:6px;font-size:13px;font-weight:800;color:var(--ink3)}\n"
  ".stfree{padding:8px 0 8px 64px;font-size:13px;font-weight:900;color:#16A34A;border-top:1px dashed var(--line)}\n"
  ".stonl{padding:10px 0 0;font-size:13px;font-weight:800;color:var(--muted);border-top:1px solid var(--line)}\n"
  ".stnav{display:flex;align-items:center;gap:8px;margin-top:16px}\n"
  ".stnav .btn{flex:1;min-height:44px}\n"
  ".stnav .iconbtn[disabled]{opacity:.35}\n"
  "/* pull down on Home to refresh */\n"
  "#ptr{position:absolute;left:50%;top:calc(var(--sb) + 6px);z-index:45;width:40px;height:40px;border-radius:50%;background:#fff;box-shadow:0 2px 10px rgba(15,23,42,.18);display:grid;place-items:center;opacity:0;transform:translate(-50%,-40px);pointer-events:none;transition:opacity .15s}\n"
  "#ptr .tc-spin{margin:0;width:20px;height:20px;animation-play-state:paused}\n"
  "#ptr.armed .tc-spin,#ptr.spin .tc-spin{animation-play-state:running}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
assert 'homeFriend' not in s, 'homeFriend still referenced'
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
