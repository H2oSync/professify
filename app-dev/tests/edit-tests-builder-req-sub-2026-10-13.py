#!/usr/bin/env python3
"""(2026-10-13) Tate: "take these out" — a requirement card's "pick one of 6 · 4 offered this spring" / "4 units · 3
offered this spring". The line is only "best ★ 3.6 Birdsall" while folded, or "nothing offered this term".
Run after edit-tests-builder-info-top-2026-10-13.py:  python3 edit-tests-builder-req-sub-2026-10-13.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
m = root / 'app-dev/tests/mutate.mjs'; ms = m.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90]); s = s.replace(a, b)
def mrep(a, b, n=1):
    global ms
    assert ms.count(a) == n, (ms.count(a), a[:90]); ms = ms.replace(a, b)

rep("sub: q.querySelector('.plq-t > span').innerText,", "sub: (q.querySelector('.plq-t > span') || {}).innerText || '',")
rep("ok(v.cards.slice(1).every(q => /offered this|nothing offered/.test(q.sub)), 'builder: a folded requirement says how many are offered (and the best professor when rated)'",
    "ok(v.cards.slice(1).every(q => !/offered this|pick one of|\\d+ units?\\b/.test(q.sub) && (/^best |^nothing offered/.test(q.sub) || q.sub === '')), 'builder: a folded requirement says only the best professor (or that nothing is offered) — no “pick one of n · n offered” (Tate 2026-10-13)'")
rep("ok(/^4 units · 2 offered this fall$/.test(ae.sub) && ae.lab === 'BEST FOR YOU'", "ok(ae.sub === '' && !ae.span && ae.lab === 'BEST FOR YOU'")
rep("sub: t(q.querySelector('.plq-t > span')), lab:", "sub: t(q.querySelector('.plq-t > span')), span: !!q.querySelector('.plq-t > span'), lab:")
rep("ok(/^pick one of 6 · 4 offered this fall · best (★ \\d\\.\\d |with )?\\w+$/.test(sp.sub) && sp.opts.length === 0, 'options: a folded requirement previews how many are offered and the best professor'",
    "ok(/^best (★ \\d\\.\\d |with )?\\w+$/.test(sp.sub) && sp.opts.length === 0, 'options: a folded requirement previews only the best professor (no “pick one of 6 · 4 offered”, Tate 2026-10-13)'")
rep("&& /pick one of \\d+/.test(v.cards[1].sub), 'options: one card per requirement, the first open; Conc. keeps its tag, a pick-one line has no “Pick 1” chip — its line already says “pick one of n” (Tate 2026-10-13)'",
    "&& !/pick one of/.test(v.cards[1].sub), 'options: one card per requirement, the first open; Conc. keeps its tag, a pick-one line has no “Pick 1” chip and no “pick one of n” (Tate 2026-10-13)'")
p.write_text(s)
mrep('''  ["foot: the pill back",''', '''  ["builder: “n offered this term” back on the card", "    const sub = [n ? '' : 'nothing offered this term', !open && best", "    const sub = [n ? n + ' offered this term' : 'nothing offered this term', !open && best", "builderOptions"],
  ["builder: an open card with nothing to say gets an empty line", "${sub ? `<span>${sub}</span>` : ''}</span>", "<span>${sub}</span></span>", "builderOptions"],
  ["foot: the pill back",''')
m.write_text(ms)
print('edit-tests-builder-req-sub: applied')

# --- follow-ups found by the run ---
s = p.read_text()
rep(r"ok(v.cards.slice(1).every(q => !/offered this|pick one of|\d+ units?\b/.test(q.sub)", r"ok(v.cards.slice(1).every(q => !/\d+ offered this|pick one of|\d+ units?\b/.test(q.sub)")
rep(r"/^1 unit\b[^|]* \| Needs a look: your report lists BUS 3306", r"/^[^|]*\| Needs a look: your report lists BUS 3306")
rep("&& lg.left === 2 && nq >= 38", "&& lg['left to graduate'] === 2 && nq >= 38")
rep("(lg.filled || 0) + (lg['in progress'] || 0) === nq - 2 && b.bar === b.leg.join(', ') + ' of ' + nq", "(lg.filled || 0) + (lg['in progress'] || 0) === nq - 2 && b.bar === b.leg.join(', ') + ' of ' + nq")
rep(r"/, 11 left of 29$/.test(sum.bar)", r"/, 11 left to graduate of 29$/.test(sum.bar)")
rep(r"/^\s*\d+ filled[\s\S]*\d+ left on your flowchart\s*Business Administration\s*\d+ requirements/.test(lt)", r"/^\s*Business Administration\s*\d+ filled[\s\S]*?\d+ left on your flowchart/.test(lt)")
p.write_text(s)
print('edit-tests-builder-req-sub (follow-ups): applied')
