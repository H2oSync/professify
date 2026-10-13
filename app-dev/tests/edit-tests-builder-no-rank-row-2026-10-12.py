#!/usr/bin/env python3
"""Tests for builder-no-rank-row-2026-10-12.py: the Builder shows no 1 · 2 · 3 chips; the order stays in the sheet.
Replayable.  python3 edit-tests-builder-no-rank-row-2026-10-12.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)
edit('check-app.mjs', [(
"ok(!after.sheet && after.rank === '1 Friends 2 Degree 3 Professors' && after.pill === '18 units · Edit' && after.rec > 0 && after.local && after.local.order.join() === 'friends,degree,professors', 'prefs: the Builder shows your order and the units, then the options; the order is also kept on the phone', after);",
"ok(!after.sheet && after.rank === '' && after.pill === '18 units · Edit' && after.rec > 0 && after.local && after.local.order.join() === 'friends,degree,professors', 'prefs: the Builder shows the units (no 1 · 2 · 3 chips — the order lives in the sheet Edit opens, Tate 2026-10-12), then the options; the order is also kept on the phone', after);",
'assert')])
edit('mutate.mjs', [
('  ["card A: registration back in the sub line", "${rankRow}${plRegBanner()}", "${rankRow}", "springCardA"],',
 '  ["card A: registration back in the sub line", "units · Edit</button></div>${plRegBanner()}", "units · Edit</button></div>", "springCardA"],', 'reaim'),
('  ["prefs: no order on the Builder", "${plUnitsTarget()} units · Edit</button></div>${rankRow}${plRegBanner()}", "${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}", "plannerPrefs"],',
 '  ["prefs: the 1 · 2 · 3 chips back on the Builder", "${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}", "${plUnitsTarget()} units · Edit</button></div><button class=\\"pl-rank\\">${prefOrder().map((x, i) => (i + 1) + \' \' + PREF_SHORT[x]).join(\' \')}</button>${plRegBanner()}", "plannerPrefs"],', 'flip'),
])
print('edit-tests-builder-no-rank-row: 1 assertion, 1 mutant re-aimed, 1 flipped')
