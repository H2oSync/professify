#!/usr/bin/env python3
"""(2026-10-13) the catalog chip sits right of the term heading (out of the top card); a folded requirement has no
"best ★ …" line. Run after edit-tests-builder-term-card-2026-10-13.py:
  python3 edit-tests-builder-catalog-top-2026-10-13.py <repo>"""
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

# the Builder view's chip, read from the view the Builder draws (these readers draw the card off-screen)
VIEW = "(() => { const d = document.createElement('div'); try { d.innerHTML = plannerView(); } catch (e) { return 'ERR ' + e.message; } return (d.querySelector('.pl-top .pl-cat') || {}).textContent || ''; })()"
rep("cr = c.querySelector('.pll-info .pc-catc'),", "cr = { textContent: " + VIEW + " },")
i = s.index("const pcSum = page => page.evaluate("); j = s.index("\n", i)
line = s[i:j]
a = "cat: [...c.querySelectorAll('.pll-info > span')].slice(1, 3).map(e => e.textContent).join(' '),"
assert line.count(a) == 1, line.count(a)
s = s[:i] + line.replace(a, "cat: " + VIEW + ", inCard: !!c.querySelector('.pc-catc'),") + s[j:]
rep("&& sum.cat === 'Quarter catalog', 'quarter catalog: the Builder’s card counts the report", "&& sum.cat === 'Quarter catalog' && !sum.inCard, 'quarter catalog: the Builder’s card counts the report")
rep("b.meta.join('|') === 'Business Administration · Financial Management|Quarter catalog'", "b.meta.join('|') === 'Business Administration · Financial Management' && b.chip === 'Quarter catalog'")
rep("big: !!c.querySelector('.pll-hd, .pll-h b'),", "big: !!c.querySelector('.pll-hd, .pll-h b'), chip: t(document.querySelector('#scroll .pl-top .pl-cat')),")
rep("cat: [...document.querySelectorAll('#scroll .pll-info > span')].slice(1, 3).map(t).join(' '),", "cat: t(document.querySelector('#scroll .pl-top .pl-cat')),")
rep("lv.first === 'pll-info' && lv.meta.length === 2", "lv.first === 'pll-info' && lv.meta.length === 1")
rep(r"ok(/^best (★ \d\.\d |with )?\w+$/.test(sp.sub) && sp.opts.length === 0, 'options: a folded requirement previews only the best professor (no “pick one of 6 · 4 offered”, Tate 2026-10-13)'",
    r"ok(sp.sub === '' && sp.opts.length === 0, 'options: a folded requirement is just its name (no “pick one of 6 · 4 offered”, no “best ★ 3.6 Birdsall”, Tate 2026-10-13)'")
rep(r"(/^best |^nothing offered/.test(q.sub) || q.sub === '')), 'builder: a folded requirement says only the best professor (or that nothing is offered)",
    r"(/^nothing offered this term$/.test(q.sub) || q.sub === '')), 'builder: a folded requirement says nothing more (or that nothing is offered)")
p.write_text(s)

for name in ('ledger: the catalog chip dropped', 'ledger: the chip says the catalog’s year again', 'ledger: a semester catalog called quarter'):
    i = ms.index('  ["' + name + '"'); j = ms.index('\n', i); ms = ms[:i] + ms[j + 1:]
mrep('''  ["foot: the pill back",''', '''  ["catalog: the chip off the term line", "  return `<div class=\\"pl-top\\"><div>${term}</div>${catChip}</div>", "  return `<div class=\\"pl-top\\"><div>${term}</div></div>", "builderMerged"],
  ["catalog: the chip says the catalog’s year again", "(/quarter/i.test(TC.audit.catalog) ? '<span class=\\"pc-catc q pl-cat\\">Quarter catalog</span>'", "(/quarter/i.test(TC.audit.catalog) ? `<span class=\\"pc-catc q pl-cat\\">${esc(TC.audit.catalog)} catalog</span>`", "builderMerged"],
  ["catalog: a semester catalog called quarter", "'<span class=\\"pc-catc s pl-cat\\">Semester catalog</span>'", "'<span class=\\"pc-catc s pl-cat\\">Quarter catalog</span>'", "pastKinds"],
  ["builder: “best ★ …” back on a folded card", "    const sub = n ? '' : 'nothing offered this term';", "    const sub = n ? (open ? '' : 'best ★ 4.0') : 'nothing offered this term';", "builderOptions"],
  ["foot: the pill back",''')
m.write_text(ms)
print('edit-tests-builder-catalog-top: applied')
