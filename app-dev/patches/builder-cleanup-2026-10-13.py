#!/usr/bin/env python3
"""The Builder's requirement cards, cleaner (Tate, 2026-10-13, on screenshots of build 23:19):
  - "clean up how this looks take the blue highlight that surrounding it away" — an open requirement card has no blue ring;
  - "include the teacher ratings doesnt need to show how many reviews" — each option's professor shows their rating
    ("Birdsall ★ 3.6"), in its colour, never the count of ratings;
  - "dont need this" (Still need · all N, and the note under it) — both leave the Builder.
Replayable on 23:19.  python3 builder-cleanup-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-cleanup: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep(""".plq-card.open{box-shadow:inset 0 0 0 2px var(--blue)}
""", "")
rep(""".plo-p{flex:none;font-size:13px;font-weight:800;color:var(--muted);max-width:40%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}""",
    """.plo-p{flex:none;font-size:13px;font-weight:800;color:var(--muted);max-width:40%;display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.plo-pn{max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}""")
rep("""<span class="plo-p">${esc(prof(c) || 'Staff')}</span></button>`; };""",
    """<span class="plo-p"><span class="plo-pn">${esc(prof(c) || 'Staff')}</span>${(r => r != null ? `<span class="rowrt rt-${rateTone(r).k}" style="color:${rateTone(r).ink}">${starI(12, rateTone(r).star)}<span class="pc-sr">rated </span>${r.toFixed(1)}</span>` : '')(s && s.prof ? ratingOf(s.prof) : null)}</span></button>`; };   /* (2026-10-13) the rating, never how many */""")
rep("""  ${concCard}${R.audit ? auditNeedCard(R.X) : stillNeedCard(L)}
  <div class="pk-note">Picks come from what your ${R.audit ? 'report says you still need' : 'flowchart still needs'}, what each class unlocks, who teaches it and who’s in it — never from ads. Your plans change only when you add a class, and are only yours until you share them. Cal Poly’s degree audit decides what counts.</div>`;""",
    """  ${concCard}`;   /* (2026-10-13) "Still need · all N" and the note under it leave the Builder (Tate: "dont need this") */""")
# the Still need card's renderer has no caller now
i = s.index("/* Everything still needed, as the Planner listed it before 2026-10-06"); j = s.index("\n}\n", s.index("function stillNeedCard(L) {", i)) + 3
s = s[:i] + s[j:]
rep("""const needHead = (label, n) => `<div class="tc-needh"><span>${label}</span><span>${n}</span></div>`;\n""", "")
rep(""".tc-sech + .tc-needh{padding-top:2px}\n""", "")
k = s.index(".tc-needh{display:flex;justify-content:space-between;"); s = s[:k] + s[s.index("\n", k) + 1:]
p.write_text(s)
print('builder-cleanup: applied')
