#!/usr/bin/env python3
"""Classes your friends are taking, as a swipe row in the Home feed (Tate, 2026-10-04).

"lets also recommend classes inbetween schedules. so it might say check out this class you havent taken
yet with this many friends in it … between schedules on the homefeed" → artifact "Classes In The Feed"
(A card / B row / C swipe row / D still-need only) → "i like c".

  · One row, after the third friend's week (after the last one with fewer friends): "SUGGESTED · CLASSES
    YOUR FRIENDS ARE TAKING", then up to 8 cards you swipe sideways: the code, the class name, up to three
    friends' faces with "N friends", and the rating of the professor most of those friends have
    ("★ 4.6 · Lee"; no rating → no chip). A card opens the class.
  · Which classes: this term's classes at least one friend is in (a section or a class with no section
    yet), not in your own classes and not on your record (class_history). Most friends first, then by code.
    Nothing to suggest → no row.
  · It is labelled "Suggested" so it never reads as a friend's post. (This bends "never mix friend and
    algorithmic content in one surface"; Tate's call, made knowingly.)
  · The "Where your friends are" card under the feed showed the same classes (top 4); the row replaces it.

Applies after pull-wheel-2026-10-04.py.
Usage: python3 feed-class-recs-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function friendClassRecs()' in s: sys.exit('already patched')
R = [
 # the list and the row
 ("""SCREENS.home = () => {
  const mine = myCodes();""",
  """/* ---- classes your friends are taking (Tate, 2026-10-04, option C of "Classes In The Feed") ---- */
/* Your record and your friends' classes compared as one course: quarter-era codes on the record
   (BUS 342) go through the planner's crosswalk to their semester code (BUS 3420). */
function recCanon(c) { const n = canonCode(c); return n && window.TCPL ? (TCPL.canon(n) || n) : n; }
function friendClassRecs() {
  /* No row until your record has loaded without an error, and none while a friend's classes failed
     to load: a suggestion built on a missing record or a half-loaded friend list would be wrong. */
  if (!Array.isArray(TC.myHistory) || TC.err.history || TC.err.friendSecs) return [];
  const hist = TC.myHistory.map(h => canonCode(h.code)).filter(Boolean);
  /* a quarter-era code needs the crosswalk (in planner.js); load it, and show the row once it's here */
  if (!window.TCPL && hist.some(c => /\s\d{3}[A-Z]?$/.test(c))) { if (!TC._recEq) TC._recEq = TC.loadPlanner().then(() => render(true)); return []; }
  const mine = new Set([...myCodes()].map(recCanon)), took = new Set(hist.map(recCanon)), by = {};
  const add = (code, fr, pk) => { const k = recCanon(code); if (!k || mine.has(k) || took.has(k)) return; const e = by[code] = by[code] || { code, who: new Set(), profs: {} }; e.who.add(fr); if (pk) (e.profs[pk] = e.profs[pk] || new Set()).add(fr); };
  TC.friends.forEach(fr => { personSecs(fr).forEach(x => add(x.code, fr, x.prof)); (PEOPLE[fr].unplaced || []).forEach(c => add(c, fr, null)); });
  /* the rating shown is the professor the most of those friends have — by friends, not sections — and
     only when one professor clearly leads (a tie shows no rating rather than an arbitrary one) */
  const lead = profs => { const ps = Object.entries(profs).map(([k, set]) => [k, set.size]).sort((a, b) => b[1] - a[1]); return ps.length && (ps.length === 1 || ps[0][1] > ps[1][1]) ? ps[0][0] : null; };
  return Object.values(by).map(e => ({ code: e.code, who: [...e.who], prof: lead(e.profs) }))
    .sort((a, b) => b.who.length - a.who.length || a.code.localeCompare(b.code)).slice(0, 8);
}
function recsRow(list) {
  if (!list.length) return '';
  return `<section class="recs" aria-label="Suggested: classes your friends are taking"><div class="recs-h">Suggested · classes your friends are taking</div><div class="recs-row">${list.map(r => {
    const rt = ratingOf(r.prof), t = rateTone(rt), nm = courseName(r.code), last = r.prof && PROFS[r.prof] ? String(PROFS[r.prof].name).trim().split(/\\s+/).pop() : '';
    return `<button class="card rmini" data-a="openClass" data-x="${esc(r.code)}"><span class="code">${esc(r.code)}</span>${nm ? `<span class="rm-t">${esc(nm)}</span>` : ''}<span class="rm-p">${avStack(r.who, 22)}<span>${r.who.length} friend${r.who.length === 1 ? '' : 's'}</span></span>${t ? `<span class="rchip rt-${t.k}" style="background:${t.bg};color:${t.ink}">${starI(13, t.star)} ${rt.toFixed(1)}${last ? `<span class="rm-ln">&nbsp;· ${esc(last)}</span>` : ''}</span>` : ''}</button>`;
  }).join('')}</div></section>`;
}
SCREENS.home = () => {
  const mine = myCodes();"""),
 # a failed record read is remembered (it used to leave TC.myHistory unset with no error)
 ("    if (!r.error) {\n      TC.myHistory = r.data || [];\n      const groups = {};",
  "    if (r.error) TC.err.history = r.error.message;\n    if (!r.error) {\n      delete TC.err.history; TC.myHistory = r.data || [];\n      const groups = {};"),
 # into the feed, after the third week
 ("""  const feed = TC.friends.length ? feedOrder().map(homeWeekCard).join('')""",
  """  const feed = TC.friends.length ? (cards => { const at = Math.min(3, cards.length); cards.splice(at, 0, recsRow(friendClassRecs())); return cards; })(feedOrder().map(homeWeekCard)).join('')"""),
 # the old card goes
 ("""  const where = {}; TC.friends.forEach(fr => [...new Set(personSecs(fr).map(s => s.code).concat(PEOPLE[fr].unplaced || []))].forEach(c => { if (!mine.has(c)) (where[c] = where[c] || new Set()).add(fr); }));
  const whereList = Object.entries(where).map(([c, set]) => [c, [...set]]).sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])).slice(0, 4);
""", ""),
 ("""
 ${whereList.length ? `<div class="sec-h">Where your friends are</div>
 <div class="card where" style="margin:0 var(--hg,16px)">${whereList.map(([c, fs]) => `<button class="li" data-a="openClass" data-x="${c}"><span class="code">${c}</span><span class="grow b" style="font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(c).short || c)}</span>${avStack(fs, 24)}<span style="font-weight:900;font-size:15px;color:var(--blue-ink);min-width:14px;text-align:right">${fs.length}</span></button>`).join('')}</div>` : ''}""", ""),
 # CSS
 (".homepg{--hg:12px}", """.homepg{--hg:12px}
.recs{min-width:0}
.recs-h{font-size:10.5px;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);padding:2px calc(var(--hg,16px) + 4px) 8px}
.recs-row{display:flex;gap:10px;overflow-x:auto;padding:0 var(--hg,16px) 2px;scroll-padding-inline:var(--hg,16px);scroll-snap-type:x proximity;scrollbar-width:none;overscroll-behavior-x:contain}
.recs-row::-webkit-scrollbar{display:none}
.hfeed.fin .recs{animation:fcIn .42s cubic-bezier(.2,.8,.2,1) .15s both}
@media (prefers-reduced-motion:reduce){.hfeed.fin .recs{animation:none}}
.rmini{flex:none;width:188px;margin:0;padding:12px;border-radius:18px;display:flex;flex-direction:column;align-items:flex-start;gap:8px;text-align:left;scroll-snap-align:start}
.rm-t{font-size:14.5px;font-weight:900;line-height:1.25;color:var(--ink);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.rmini .rchip{max-width:100%;white-space:nowrap}
.rm-ln{overflow:hidden;text-overflow:ellipsis;min-width:0}
.rm-p{display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:800;color:var(--ink3);margin-top:auto}"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
