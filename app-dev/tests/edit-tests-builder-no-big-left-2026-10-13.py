#!/usr/bin/env python3
"""(2026-10-13) the Builder top card has no big "N left" heading; the legend's amber entry says "N left to graduate"
(or "N left on your flowchart"). Every reader of .pll-h reads that legend entry instead.
Run after edit-tests-builder-catalog-chip-2026-10-13.py:  python3 edit-tests-builder-no-big-left-2026-10-13.py <repo>"""
import sys, pathlib, re
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
m = root / 'app-dev/tests/mutate.mjs'; ms = m.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90]); s = s.replace(a, b)
n = s.count("querySelector('.pll-h')") + s.count("querySelector('#scroll .pll-h')")
assert n == 9, n
s = s.replace("querySelector('.pll-h')", "querySelector('.pll-leg .l')").replace("querySelector('#scroll .pll-h')", "querySelector('#scroll .pll-leg .l')")
# the legend's counts: the amber entry's number is still its first word
rep("const leg = {}; [...c.querySelectorAll('.pll-leg > span')].forEach(e => { leg[e.className] = +t(e).split(' ')[0]; });", "const leg = {}; [...c.querySelectorAll('.pll-leg > span')].forEach(e => { leg[e.className] = +t(e).split(' ')[0]; });")
rep("b.order.slice(0, 4).join() === 'pll-hd,pll-bar,pll-leg,pll-info'", "b.order.slice(0, 3).join() === 'pll-bar,pll-leg,pll-info' && !b.big")
rep("meta: [...c.querySelectorAll('.pll-info > span')].map(t), h:", "big: !!c.querySelector('.pll-hd, .pll-h b'), meta: [...c.querySelectorAll('.pll-info > span')].map(t), h:")
rep("'builder: one card on top — “2 left to graduate”, the three-way bar and its legend", "'builder: one card on top — no big number (Tate 2026-10-13: “repetitive”); the three-way bar and its legend ending “2 left to graduate”")
rep("ok(v && /^pll-hd/.test(v.first) &&", "ok(v && /^pll-bar/.test(v.first) &&")
rep("'past kinds: the card opens with what’s left on your flowchart (the ledger),", "'past kinds: the card opens with the ledger (no big number; the legend says what’s left on your flowchart),")
rep("lv.segs.join() === ['f', 'p', 'l', 'u'].filter(k => lv.leg[k]).join()", "lv.segs.join() === ['f', 'p', 'l', 'u'].filter(k => lv.leg[k]).join() && lv.legText[lv.legText.length - 1] === '2 left to graduate'")
# the flowchart readers of the card's text: "F filled … L left" is now "F filled … L left on your flowchart"
rep(r"(await withLeft(page)).match(/(\d+) filled\s*(?:\d+ in progress\s*)?\d+ left/)[1]", r"(await withLeft(page)).match(/(\d+) filled\s*(?:\d+ in progress\s*)?\d+ left on your flowchart/)[1]", 5)
rep(r"/^\s*\d+\s*left on your flowchart\s*\d+ filled[\s\S]*\d+ left\s*Business Administration\s*\d+ requirements/.test(lt)", r"/^\s*\d+ filled[\s\S]*\d+ left on your flowchart\s*Business Administration\s*\d+ requirements/.test(lt)")
rep(r"ok(/2 filled\s*4 in progress\s*27 left/.test(t)", r"ok(/2 filled\s*4 in progress\s*27 left on your flowchart/.test(t)")
rep(r"lg.label === '2 filled, 4 in progress, 27 left of 33'", r"lg.label === '2 filled, 4 in progress, 27 left on your flowchart of 33'")
rep(r"ok(/3 filled\s*4 in progress\s*26 left/.test(t)", r"ok(/3 filled\s*4 in progress\s*26 left on your flowchart/.test(t)")
p.write_text(s)
ms = ms.replace('  ["foot: the pill back",', '''  ["ledger: the big number back", "  const top = `<div class=\\"card pll\\">${bar}", "  const top = `<div class=\\"card pll\\"><div class=\\"pll-h\\"><b>${reqs.length}</b><span>left</span></div>${bar}", "builderMerged"],
  ["ledger: the legend's left loses its words", "['l', nL, R.audit ? 'left to graduate' : 'left on your flowchart']", "['l', nL, 'left']", "plannerMarkDone"],
  ["foot: the pill back",''', 1)
m.write_text(ms)
print('edit-tests-builder-no-big-left: applied')
