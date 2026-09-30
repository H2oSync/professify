#!/usr/bin/env python3
"""Tapping a class on a friend's week opens the same preview as My Classes and Plans (Tate, 2026-09-30).

"when you click on a class on the homepage it should do the same as on my classes and plans where it
first gives you a preview this preview should also show your friends in the classes of friends."

- Home friend cards, a friend's page week and a friend's shared-plan grids pass blockAct:'secSheet'
  (they used to jump straight to the class page).
- The preview (SHEETS.sec) finds the section in the seat feed, your week, or any friend's week, and
  lists who is in it: "In this section" (you, then accepted friends in that exact section) and
  "Other sections" (friends, or you, in the same class at another time). Friends only, as everywhere.

Run from the repo root: python3 app-dev/patches/home-sec-preview-2026-09-30.py (idempotent; each
anchor must match once).
"""
import sys, pathlib
P = pathlib.Path('app/index.html'); s = P.read_text()
MARK = '/* The preview names who is in the class'
if MARK in s: print('already applied'); sys.exit(0)
def sub(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n} times: {a[:80]!r}')
    s = s.replace(a, b)

sub("grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, shared, one: true, fit: 30, H: 300 })",
    "grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300 })")
sub("grid(secs, { sel: S.homeDays['plan:' + id + ':' + k], act: 'homeDay', key: 'plan:' + id + ':' + k, shared: both, one: true, H: 260 })",
    "grid(secs, { sel: S.homeDays['plan:' + id + ':' + k], act: 'homeDay', key: 'plan:' + id + ':' + k, blockAct: 'secSheet', shared: both, one: true, H: 260 })")
sub("grid(secs, { sel: S.homeDays['f:' + id], act: 'homeDay', key: 'f:' + id, shared, one: true, H: 280 })",
    "grid(secs, { sel: S.homeDays['f:' + id], act: 'homeDay', key: 'f:' + id, blockAct: 'secSheet', shared, one: true, H: 280 })")

sub("""SHEETS.sec = ({ code, id }) => {
  const s = SEC[id] || personSecs('me').find(x => x.id === id); if (!s) return '';
  const c = course(code), fr = friendsInSec(id), inP = TC.plans[S.plan].includes(id), w = !!TC.watches[id];""",
"""/* The preview names who is in the class: you and accepted friends in this exact section first, then
   anyone in the same class at another time. A friend's week can hold a section the seat feed
   doesn't (it left the term list), so the section is looked up there too. */
function secPeople(code, id) {
  const meIn = personSecs('me').some(x => x.id === id), meCode = myCodes().has(code);
  const here = (meIn ? ['me'] : []).concat(friendsInSec(id));
  const other = (!meIn && meCode ? ['me'] : []).concat(friendsIn(code).filter(f => !here.includes(f)));
  return { here, other };
}
function secPeopleRow(ids, label) {
  if (!ids.length) return '';
  return `<div class="muted b" style="font-size:12.5px;letter-spacing:.04em;text-transform:uppercase;margin-top:14px">${label}</div>
 <div class="row" style="gap:6px 14px;flex-wrap:wrap;margin-top:4px">${ids.map(f => f === 'me'
    ? `<span class="row" style="gap:6px;min-height:44px">${pav('me', 28, 10)}<span class="b" style="font-size:14px">You</span></span>`
    : `<button class="row" style="gap:6px;min-height:44px" data-a="openFriend" data-x="${esc(f)}">${pav(f, 28, 10)}<span class="b" style="font-size:14px">${esc(PEOPLE[f].short)}</span></button>`).join('')}</div>`;
}
SHEETS.sec = ({ code, id }) => {
  const s = SEC[id] || personSecs('me').find(x => x.id === id) || TC.friends.map(f => personSecs(f).find(x => x.id === id)).find(Boolean); if (!s) return '';
  const c = course(code), who = secPeople(code, id), inP = TC.plans[S.plan].includes(id), w = !!TC.watches[id];""")
sub(""" ${fr.length ? `<div class="row" style="margin-top:12px;gap:8px">${avStack(fr, 28)}<span class="b" style="font-size:14px">${fr.map(f => esc(PEOPLE[f].short)).join(', ')}</span></div>` : ''}
 <div style="display:grid;gap:8px;margin-top:18px"><button class="btn" data-a="openClass" data-x="${code}">View class</button>""",
""" ${secPeopleRow(who.here, 'In this section')}${secPeopleRow(who.other, 'Other sections')}
 <div style="display:grid;gap:8px;margin-top:18px"><button class="btn" data-a="openClass" data-x="${code}">View class</button>""")
P.write_text(s); print('applied')
