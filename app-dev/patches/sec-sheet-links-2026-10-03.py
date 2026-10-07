#!/usr/bin/env python3
"""The section preview: the professor and the friends in it look tappable, and the campus is gone
(Tate, 2026-10-03, on a screenshot of a friend's BIO 3312 S02 sheet: "make it so you can click a
professor from here. also make it so you can click a friend from here too. take out Cal poly san luis
obispo.").

- The professor is the class page's own professor row: photo initials, name, their real rating (or
  "No ratings yet"), and a chevron. It opens the professor page. With no instructor listed it reads
  "Instructor not assigned / Listed as Staff for now", like the class page, and is not a button.
- The time and the seats share one line under the title. With the professor row the sheet is about
  60px taller than before; the dimmed page above it still closes it.
- Opening the professor or friend whose page is already showing (a friend's page → their class → their
  chip) just closes the sheet instead of stacking the same page twice.
- Friends under "In this section" / "Other sections" are pill chips with a chevron. They already
  opened the friend's page, but they looked like plain text. "You" stays plain.
- The campus ("Cal Poly-San Luis Obispo") is no longer shown. It is PeopleSoft's Location field,
  which is the campus, not the room, so on a one-campus app it never told anyone anything.

Applies after share-edge-plan-2026-09-30.py (build 2026-09-30 20:00).
Usage: python3 sec-sheet-links-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function secProfRow' in s: sys.exit('already patched')
R = [
 # the professor row, shared by the class page and the section preview
 ("SHEETS.sec = ({ code, id }) => {\n",
  "/* The professor as a tappable row (the class page's look). No instructor listed: plain text, no button. */\n"
  "function secProfRow(pid) {\n"
  "  if (!pid || !PROFS[pid]) return `<div class=\"profrow\" style=\"margin-top:12px\">${avL('?', 40, 14)}<div class=\"grow\"><div class=\"nm\">Instructor not assigned</div><div class=\"muted b\" style=\"font-size:13px\">Listed as Staff for now</div></div></div>`;\n"
  "  const r = ratingOf(pid);\n"
  "  return `<button class=\"profrow\" style=\"margin-top:12px\" data-a=\"openProf\" data-x=\"${esc(pid)}\" aria-label=\"${esc(profName(pid))}, see professor\">${profAv(pid, 40, 14)}<div class=\"grow\"><div class=\"nm\">${esc(profName(pid))}</div><div class=\"row b\" style=\"gap:4px;font-size:14px\">${r != null ? starI(13, rateTone(r).star) + `<span class=\"rt-${rateTone(r).k}\" style=\"color:${rateTone(r).ink}\">${r.toFixed(1)}</span><span class=\"muted\" style=\"font-weight:700\">&nbsp;· ${nRatings(PROFS[pid].count)}</span>` : '<span class=\"muted\">No ratings yet</span>'}</div></div><span style=\"color:var(--purple)\">${ic('chevR', 20)}</span></button>`;\n"
  "}\n"
  "SHEETS.sec = ({ code, id }) => {\n"),
 # time + seats on one line, the professor row under it, and no campus
 (" <h3 style=\"margin-top:10px\">${esc(c.title)}</h3><div class=\"muted b\">${esc(profName(s.prof))} · ${secWhen(s)}</div>\n"
  " <div class=\"b\" style=\"margin-top:6px;font-size:14px\">${secSeatText(s)}${s.location ? ` <span class=\"muted\">· ${esc(s.location)}</span>` : ''}</div>\n",
  " <h3 style=\"margin-top:10px\">${esc(c.title)}</h3><div class=\"b secwhen\" style=\"margin-top:4px;font-size:14px\"><span class=\"muted\">${secWhen(s)}</span> · ${secSeatText(s)}</div>\n"
  " ${secProfRow(s.prof)}\n"),
 # friends as chips with a chevron; "You" stays plain
 ("    : `<button class=\"row\" style=\"gap:6px;min-height:44px\" data-a=\"openFriend\" data-x=\"${esc(f)}\">${pav(f, 28, 10)}<span class=\"b\" style=\"font-size:14px\">${esc(PEOPLE[f].short)}</span></button>`).join('')}</div>`;\n",
  "    : `<button class=\"secppl\" data-a=\"openFriend\" data-x=\"${esc(f)}\" aria-label=\"${esc(PEOPLE[f].name)}, see their page\">${pav(f, 28, 10)}<span class=\"b\">${esc(PEOPLE[f].short)}</span>${ic('chevR', 15, 2.6)}</button>`).join('')}</div>`;\n"),
 # the page you are already on: close the sheet, don't push it again
 ("  openProf: (id, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim()) recentAdd('p', id); UI.champ = false; go('profDetail', { id }); },\n",
  "  openProf: (id, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim()) recentAdd('p', id); UI.champ = false; if (onPage('profDetail', id)) { UI.sheet = null; return render(true); } go('profDetail', { id }); },\n"),
 ("  openFriend: id => { UI.champ = false; if (!id) return; if (id === 'me') return setTab('schedule'); if (TC.user) loadFriendPlans(); go('friend', { id }); },\n",
  "  openFriend: id => { UI.champ = false; if (!id) return; if (id === 'me') return setTab('schedule'); if (onPage('friend', id)) { UI.sheet = null; return render(true); } if (TC.user) loadFriendPlans(); go('friend', { id }); },\n"),
 ("function go(s, p) {",
  "/* Is this exact page (screen + id) the one showing? */\nfunction onPage(s, id) { const e = cur(); return !!e && e.s === s && !!e.p && e.p.id === id; }\nfunction go(s, p) {"),
 # styles
 (".profrow .nm{color:var(--purple-ink);font-weight:900;font-size:17px}\n",
  ".profrow .nm{color:var(--purple-ink);font-weight:900;font-size:17px}\n"
  ".secppl{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:4px 10px 4px 5px;border-radius:999px;background:var(--bg);font-size:14px}\n"
  ".secppl svg{color:var(--muted)}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
