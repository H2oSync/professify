#!/usr/bin/env python3
"""No "No classes today" under a friend's name (Tate, 2026-10-09, on Braden's Home card and page:
"take the no classes today out").

A friend with classes this term but none today still gets the green ring (free), but no status line
saying so — on Home's card, their page, the Friends list, a chat's header, search results and the top of
their story. A story's day still says "No classes today · <name> is free all <day>" where the classes
would be, and Champ still answers "is <name> free?" in words. Other statuses ("In BUS 3431 till 11a",
"Free till 12:10p", "Done for the day", "No classes added") are unchanged.
Usage: python3 no-classes-today-line-2026-10-09.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'no-classes-today-line (2026-10-09)' in s:
    sys.exit('already patched')
def one(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:100]); s = s.replace(old, new)

one("""  return { c: '#16A34A', t: 'No classes today', free: true };""",
    """  return { c: '#16A34A', t: 'No classes today', free: true, quiet: true };   /* green ring, no line under the name (no-classes-today-line (2026-10-09)) */""")
# Home card
one("""    ${st && st.free !== null ? `<div style="font-size:12.5px;font-weight:800;color:${st.c || 'var(--muted)'};margin-top:3px">● ${esc(st.t)}</div>` : ''}</div>""",
    """    ${st && st.free !== null && !st.quiet ? `<div style="font-size:12.5px;font-weight:800;color:${st.c || 'var(--muted)'};margin-top:3px">● ${esc(st.t)}</div>` : ''}</div>""")
# Friends list row
one("""<div style="font-weight:900;font-size:16px">${esc(PEOPLE[id].name)}</div><div class="b" style="font-size:13px;color:${st.c || 'var(--muted)'}">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</div></div>""",
    """<div style="font-weight:900;font-size:16px">${esc(PEOPLE[id].name)}</div>${st.quiet ? '' : `<div class="b" style="font-size:13px;color:${st.c || 'var(--muted)'}">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</div>`}</div>""")
# search results
one("""${PEOPLE[id].handle ? `<span class="muted">@${esc(PEOPLE[id].handle)} · </span>` : ''}<span style="color:${st.c || 'var(--muted)'}">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</span>""",
    """${PEOPLE[id].handle ? `<span class="muted">@${esc(PEOPLE[id].handle)}${st.quiet ? '' : ' · '}</span>` : ''}${st.quiet ? '' : `<span style="color:${st.c || 'var(--muted)'}">${st.free === null ? esc(st.t) : '● ' + esc(st.t)}</span>`}""")
# chat header
one("""${st && st.free !== null ? `<div class="b" style="font-size:12.5px;color:${st.c || 'var(--muted)'}">● ${esc(st.t)}</div>` : ''}""",
    """${st && st.free !== null && !st.quiet ? `<div class="b" style="font-size:12.5px;color:${st.c || 'var(--muted)'}">● ${esc(st.t)}</div>` : ''}""")
# friend page
one("""${st && st.free !== null ? `<div class="mestatus" style=""", """${st && st.free !== null && !st.quiet ? `<div class="mestatus" style=""")
# top of a story's sheet
one("""${esc(p.name)}</span>${st.free !== null || st.t ? `<span class="b" style="display:block;font-size:13.5px;color:var(--muted)">""",
    """${esc(p.name)}</span>${!st.quiet && (st.free !== null || st.t) ? `<span class="b" style="display:block;font-size:13.5px;color:var(--muted)">""")
f.write_text(s); print('patched', f)
