#!/usr/bin/env python3
"""(2026-10-13) the Builder top card's catalog chip says only "Quarter catalog" / "Semester catalog"; no report date.
Run after edit-tests-misc-2026-10-13.py:  python3 edit-tests-builder-catalog-chip-2026-10-13.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
m = root / 'app-dev/tests/mutate.mjs'; ms = m.read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
def mrep(a, b):
    global ms
    assert ms.count(a) == 1, (ms.count(a), a[:90]); ms = ms.replace(a, b)
rep("sum.cat === 'Fall Quarter 2023 catalog report · Oct 9, 2026'", "sum.cat === 'Quarter catalog'")
rep("v.cat === '2026-2027 catalog', 'past (report): “2 left to graduate” on top, and the catalog your report judges you",
    "v.cat === 'Semester catalog', 'past (report): “2 left to graduate” on top, and the kind of catalog your report judges you")
rep("b.meta.join('|') === `Business Administration · Financial Management|Fall Quarter 2023 catalog|report · Oct 9, 2026|${nq} requirements`",
    "b.meta.join('|') === `Business Administration · Financial Management|Quarter catalog|${nq} requirements`")
rep("v.cat === 'Fall Quarter 2023 catalog report · Oct 8, 2026' && v.h === '2 left to graduate'",
    "v.cat === 'Quarter catalog 2 requirements' && v.h === '2 left to graduate'")
p.write_text(s)
mrep("""  ["ledger: the catalog chip dropped", "<span class=\\"pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}\\">${esc(TC.audit.catalog)} catalog</span><span>report", "<span>report", "builderMerged"],""",
     """  ["ledger: the catalog chip dropped", "${X && TC.audit.catalog ? (/quarter/i.test(TC.audit.catalog) ?", "${false ? (/quarter/i.test(TC.audit.catalog) ?", "builderMerged"],
  ["ledger: the chip says the catalog’s year again", "'<span class=\\"pc-catc q\\">Quarter catalog</span>' : '<span class=\\"pc-catc s\\">Semester catalog</span>') : ''}${tot", "`<span class=\\"pc-catc q\\">${esc(TC.audit.catalog)} catalog</span>` : '<span class=\\"pc-catc s\\">Semester catalog</span>') : ''}${tot", "builderMerged"],
  ["ledger: a semester catalog called quarter", "<span class=\\"pc-catc s\\">Semester catalog</span>') : ''}${tot", "<span class=\\"pc-catc s\\">Quarter catalog</span>') : ''}${tot", "pastKinds"],""")
m.write_text(ms)
print('edit-tests-builder-catalog-chip: applied')
