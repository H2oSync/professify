#!/usr/bin/env python3
"""A class with no set time shows in Add to your week, and the add sheet says where it went (Tate, 2026-10-09).

Run after no-classes-today-line-2026-10-09.py. Edits app/index.html only.

Tate: "i am trying to add classes to plans but once i added one it wont let me add another like human
recources". His screenshot: Add to your week for BUS 3384A V01 (Human Resources Management Project,
"Time not posted"), Plan B ticked, Plan B's week showing only BUS 3347, "BUS 3384A has no set time, so it
isn't drawn.", "BUS 3384A V01 is in Plan B." and only a Remove button. His real plans (read in the phone
preview): A and B both hold BUS 3347 S02 and BUS 3384A V01. Adding worked; nothing on the sheet showed it.
A class with no time had no place on the sheet's week, so a plan that had it looked like a plan without it,
and the sheet offered only Remove.

  1. Add to your week draws an ANYTIME tray under its week (Home's tray, Tate's A3): the place's classes
     with no set time, as two-line chips in the place's colour. The section being added glows in the place's
     colour like the lit block on the week; one already there is a plain chip; one it would swap out is
     faded and struck through. The "has no set time, so it isn't drawn" line is gone. With nothing timed at
     all, the tray is the week.
  2. The note says where it is: "BUS 3384A V01 is already in Plan B — under Anytime, since it has no set
     time." / "Fits Plan B — it has no set time, so it goes under Anytime."
  3. Schedule › Plans: the "No set time" card says "Anytime" and uses the same two-line chips, in the
     plan's colour, like Home.
"""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
P = ROOT / 'app' / 'index.html'
s = P.read_text()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f'plans-anytime: expected {n} of {a[:90]!r}, found {c}')
    s = s.replace(a, b)


# one helper for the two-line code chip (Home's, lifted out of homeWeekCard)
rep("""  const anyCode = c => { const i = c.indexOf(' '); return i < 0 ? `<span>${esc(c)}</span>` : `<span>${esc(c.slice(0, i))}</span><span>${esc(c.slice(i + 1))}</span>`; };
""", """  const anyCode = anyCodeHtml;
""")
rep("""function homeWeekCard(id) {""",
    """/* A class code on two lines, like a narrow block on the week ("BUS" over "4418A") — the Anytime chips. */
function anyCodeHtml(c) { const i = c.indexOf(' '); return i < 0 ? `<span>${esc(c)}</span>` : `<span>${esc(c.slice(0, i))}</span><span>${esc(c.slice(i + 1))}</span>`; }
function homeWeekCard(id) {""")

# 1. the add sheet: an Anytime tray under its week
rep("""  const timed = secs.some(x => !x.async && x.s != null && x.e != null);""",
    """  const timed = secs.some(x => !x.async && x.s != null && x.e != null);
  /* classes with no set time: an Anytime tray under the week (2026-10-09) — so a plan that has one shows it */
  const atGrid = x => !x.async && x.s != null && x.e != null && [...x.days].some(d => DAYS.includes(d));
  const anyS = o.other ? [] : secs.filter(x => !atGrid(x)), replIds = new Set(o.repl.map(x => x.id)), untimed = !atGrid(s);
  /* why it's under Anytime: no time at all, or a time on Saturday/Sunday only (the week has no column for it) */
  const whyAny = s.async || s.noTime || s.s == null || s.e == null ? 'it has no set time' : 'it meets only on the weekend';
  const anyTray = anyS.length ? `<div class="anyrow at-any" role="group" aria-label="${esc(o.where)}: classes with no set time"><span class="any-h">Anytime</span>${anyS.map(x => {
    const lit = x.id === sh.id && (!o.inIt || adding) && !added, out = replIds.has(x.id), lab = x.code + (secLabel(x.sec) ? ' ' + secLabel(x.sec) : '') + ' · ' + secWhen(x);
    return `<span class="any-c${lit ? ' new' : ''}${out ? ' out' : ''}" role="img" aria-label="${esc(lab + (lit ? ' — going in' : out ? ' — swapped out' : ''))}" title="${esc(lab)}">${anyCodeHtml(x.code)}</span>`; }).join('')}</div>` : '';""")
rep("""    : `<div class="empty"><b>Nothing to draw yet</b>${s.async || s.noTime ? 'This section has no set time.' : ''}</div>`;
  const foot = timed && (s.async || s.noTime) ? `<div class="at-foot">${esc(s.code)} has no set time, so it isn’t drawn.</div>` : '';""",
    """    : anyTray ? '' : `<div class="empty"><b>Nothing to draw yet</b></div>`;""")
rep(""" <div class="at-week">${week}${foot}</div>""", """ <div class="at-week">${week}${anyTray}</div>""")

# 2. the note says where it is
rep("""  else if (o.inIt) { note = `${nm(s)} is in ${o.where}.`;""",
    """  else if (o.inIt) { note = untimed ? `${nm(s)} is already in ${o.where} — under Anytime, since ${whyAny}.` : `${nm(s)} is in ${o.where}.`;""")
rep("""  else { note = o.mine ? 'Fits your week.' : `Fits Plan ${o.P}.`; tn = 'ok'; btn = go(`Add to ${o.where}`); }""",
    """  else { note = (o.mine ? 'Fits your week' : `Fits Plan ${o.P}`) + (untimed ? ` — ${whyAny}, so it goes under Anytime.` : '.'); tn = 'ok'; btn = go(`Add to ${o.where}`); }""")

# the tray inside the sheet's card, in the place's colour; the one going in glows
rep(""".at-foot{padding:6px 20px 0;font-size:13px;font-weight:800;color:var(--muted)}""",
    """.at-week .anyrow{margin:10px 10px 0}
.at-week > .anyrow:first-child{margin-top:0}
.at-week .any-h{color:var(--ink4)}
.addto .any-c{background:var(--pc-soft2);color:var(--pc-ink)}
.addto .any-c.new{background:var(--pc);color:#fff;box-shadow:0 0 0 2.5px var(--card),0 6px 18px var(--pc-glow)}
.addto .any-c.out{background:transparent;color:var(--muted);box-shadow:inset 0 0 0 2px var(--muted2);text-decoration:line-through}""")

# 3. Schedule › Plans: "Anytime", the same chips, the plan's colour — and the same on-the-week test as the sheet and
#    Home, so a Saturday-only section is under Anytime here too (it was on neither the grid nor the card)
rep("""    const secs = planSecs(S.plan), timed = secs.filter(s => !s.async && s.s != null), any = secs.filter(s => s.async || s.s == null), miss = planMissing(S.plan);""",
    """    const onWk = s => !s.async && s.s != null && s.e != null && [...s.days].some(d => DAYS.includes(d));
    const secs = planSecs(S.plan), timed = secs.filter(onWk), any = secs.filter(s => !onWk(s)), miss = planMissing(S.plan);""")
rep("""  ${any.length ? `<div class="card anytime"><span style="font-weight:900;font-size:16px;margin-right:4px">No set time</span>${any.map(s => `<button class="code" style="font-size:14px;padding:7px 12px" data-a="secSheet" data-x="${s.code}" data-y="${esc(s.id)}">${s.code}</button>`).join('')}</div>` : ''}""",
    """  ${any.length ? `<div class="card anytime" role="group" aria-label="Plan ${S.plan}: classes with no set time"><span style="font-weight:900;font-size:16px;margin-right:4px">Anytime</span>${any.map(s => `<button class="any-c" data-a="secSheet" data-x="${s.code}" data-y="${esc(s.id)}" aria-label="${esc(s.code)}">${anyCodeHtml(s.code)}</button>`).join('')}</div>` : ''}""")

P.write_text(s)
print('plans-anytime-2026-10-09: ok')
