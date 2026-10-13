#!/usr/bin/env python3
"""(2026-10-13) Tate: "have this Business Administration · Financial Management Quarter catalog above the progress line"
and "take this out 55 requirements". Who you are opens the Builder's top card; no "n requirements". Readers take N from
the bar's label ("… of N"). Run after edit-tests-builder-no-big-left-2026-10-13.py:
  python3 edit-tests-builder-info-top-2026-10-13.py <repo>"""
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

NN = r"""(((c.querySelector('.pll-bar') || { getAttribute: () => '' }).getAttribute('aria-label') || '').match(/of (\d+)$/) || [])[1] || ''"""
rep("(c.querySelector('.pll-n') || {}).textContent || ''", NN, 7)
rep("+t(c.querySelector('.pll-n')).split(' ')[0] || 0", "+(" + NN + ") || 0")
rep("b.order.slice(0, 3).join() === 'pll-bar,pll-leg,pll-info' && !b.big", "b.order.slice(0, 3).join() === 'pll-info,pll-bar,pll-leg' && !b.big")
rep("const nq = b ? +(b.meta[b.meta.length - 1] || '').split(' ')[0] : 0;", r"const nq = b ? +((String(b.bar).match(/of (\d+)$/) || [])[1] || 0) : 0;")
rep("b.meta.join('|') === `Business Administration · Financial Management|Quarter catalog|${nq} requirements`", "b.meta.join('|') === 'Business Administration · Financial Management|Quarter catalog'")
rep("v.cat === 'Quarter catalog 2 requirements'", "v.cat === 'Quarter catalog'")
rep("lv.meta[lv.meta.length - 1] === `${lv.n} requirements`", "lv.first === 'pll-info' && lv.meta.length === 2")
rep("ok(v && /^pll-bar/.test(v.first) &&", "ok(v && /^pll-info/.test(v.first) &&")
p.write_text(s)

mrep('  ["ledger: no “n requirements”", ', '  ["ledger: “n requirements” back", ')
i = ms.index('["ledger: “n requirements” back"'); j = ms.index('\n', i)
ms = ms[:i] + '["ledger: “n requirements” back", "${tot ? `<span class=\\"pc-inp\\">· ${tot} units to go</span>` : \'\'}</div>`;", "${tot ? `<span class=\\"pc-inp\\">· ${tot} units to go</span>` : \'\'}<span class=\\"pll-n\\">${N} requirements</span></div>`;", "builderOptions"],' + ms[j:]
mrep('"  const top = `<div class=\\"card pll\\">${bar}", "  const top = `<div class=\\"card pll\\"><div class=\\"pll-h\\"><b>${reqs.length}</b><span>left</span></div>${bar}", "builderMerged"],',
     '"  const top = `<div class=\\"card pll\\">${/<span/.test(meta) ? meta : \'\'}${bar}", "  const top = `<div class=\\"card pll\\"><div class=\\"pll-h\\"><b>${reqs.length}</b><span>left</span></div>${/<span/.test(meta) ? meta : \'\'}${bar}", "builderMerged"],\n  ["ledger: who you are under the bar again", "  const top = `<div class=\\"card pll\\">${/<span/.test(meta) ? meta : \'\'}${bar}", "  const top = `<div class=\\"card pll\\">${bar}${/<span/.test(meta) ? meta : \'\'}", "builderMerged"],')
m.write_text(ms)
print('edit-tests-builder-info-top: applied')
