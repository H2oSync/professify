#!/usr/bin/env python3
"""Two Schedule asks (Tate, 2026-10-12):
  1. "this view should show the professors rating. same with the plans view." — My Classes' and Plans' day lists name
     the professor with their rating ("Thomas Bonczek ★ 3.2 · Full"), in the rating's colour, as a friend's class sheet does.
  2. "Be consistent … when I'm on my schedule and I click one, instead of having that little preview, it opens up the
     actual class … the initial should just show that little pop-up." — My Classes on the term you're in (Fall) opens
     the section's sheet (class, term, time, seats, professor, who's in it, View class) from its week, its day list and
     its Anytime row, as a friend's week does. A class with no section, and a term that's neither, still open the page.
Replayable on 18:05.  python3 schedule-rows-2026-10-12.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'schedule-rows: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)

# a helper beside secSeatText: the professor and their rating, for a day-list row
rep("""function courseSeats(code) {""", """/* (2026-10-12) a day-list row's professor: the name, then the rating in its colour ("★ 3.2"), when PolyRatings has one */
function rowProf(pk) {
  const r = ratingOf(pk);
  return `${esc(profName(pk))}${r != null ? ` <span class="rowrt rt-${rateTone(r).k}" style="color:${rateTone(r).ink}">${starI(12, rateTone(r).star)}<span class="pc-sr">rated </span>${r.toFixed(1)}</span>` : ''}`;
}
function courseSeats(code) {""")
rep("""*{box-sizing:border-box;margin:0;padding:0}""", """*{box-sizing:border-box;margin:0;padding:0}
.rowrt{display:inline-flex;align-items:center;gap:2px;font-weight:900;white-space:nowrap}.rowrt svg{flex:none}""")
# My Classes' day list
rep("""<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))}${seat(s)}${wl(s)}</span>""",
    """<span class="muted b" style="display:block;font-size:14px">${rowProf(s.prof)}${seat(s)}${wl(s)}</span>""")
# Plans' day list
rep("""<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))} · ${secSeatText(s)}</span>""",
    """<span class="muted b" style="display:block;font-size:14px">${rowProf(s.prof)} · ${secSeatText(s)}</span>""")
# My Classes on the term you're in: the section's sheet first, like a friend's week
rep("""  const act = s => o.now || o.other ? `data-a="openClass" data-x="${esc(s.code)}"${o.now ? ' data-y="now"' : ''}` : `data-a="secSheet" data-x="${esc(s.code)}" data-y="${esc(s.id)}"`;""",
    """  /* (2026-10-12) the term you're in opens the section's sheet too (Tate: "the initial should just show that little pop-up") */
  const act = s => o.other && !o.now ? `data-a="openClass" data-x="${esc(s.code)}"` : `data-a="secSheet" data-x="${esc(s.code)}" data-y="${esc(s.id)}"`;""")
rep("""  return mineAgenda(ts.secs, ts.unplaced, { now: isNowT, other: !isNowT, label: tm.label, grid: { sel: S.schedDay, act: 'schedDay', blockAct: 'openClass', H: 330, noNow: true } });""",
    """  return mineAgenda(ts.secs, ts.unplaced, { now: isNowT, other: !isNowT, label: tm.label, grid: { sel: S.schedDay, act: 'schedDay', blockAct: isNowT ? 'secSheet' : 'openClass', H: 330, noNow: true } });""")
p.write_text(s)
print('schedule-rows: applied')
