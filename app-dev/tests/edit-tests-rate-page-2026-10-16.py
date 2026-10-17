#!/usr/bin/env python3
"""(2026-10-16) Keeps the older desktop checks true after rate-page-2026-10-16.py (website; marker 'rate-page (2026-10-16)'):
  check-desktop-look.mjs  the Rate tab opens the Rate PAGE (not the "Review a professor" modal) and is lit like the other tabs;
                          the Rate page's buttons / cards are the app's blue and white (the picker's soft-purple rows are gone from this tab).
Usage: python3 edit-tests-rate-page-2026-10-16.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
def edit(name, pairs):
    p = root / 'app-dev/tests' / name; s = p.read_text()
    if 'rate-page (2026-10-16)' in s: sys.exit('already edited ' + name)
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:100]); s = s.replace(a, b)
    s = s.rstrip('\n') + '\n/* rate-page (2026-10-16): this file was updated by edit-tests-rate-page-2026-10-16.py */\n'
    p.write_text(s); print('edited', p)

edit('check-desktop-look.mjs', [
 ("""  ok(await page.evaluate(() => { const b = document.getElementById('rlBack'); return !!b && getComputedStyle(b).display !== 'none' && b.getBoundingClientRect().height > 0; }), 'Rate opens Review a professor');""",
  """  ok(await page.evaluate(() => { const v = document.getElementById('view-rate'), b = document.getElementById('rlBack'); return !!v && v.classList.contains('active') && v.getBoundingClientRect().height > 0 && !b.classList.contains('open') && document.getElementById('tab-rate').classList.contains('active'); }), 'Rate opens the Rate page (not the Review a professor sheet), and its tab is lit');"""),
 ("""  r = await page.evaluate(() => { const row = document.querySelector('#rlLists > div:not(.rl-term):not(:first-child)'); return row && getComputedStyle(row).backgroundColor; });
  ok(r === 'rgb(243, 238, 255)', 'the Rate sheet\\'s professors are the app\\'s soft-purple rows', r);""",
  """  r = await page.evaluate(() => { const b = document.querySelector('#rtLists .rt-rate'), c = document.querySelector('#rtRail .rt-card'); return b && c && { btn: getComputedStyle(b).backgroundColor, card: getComputedStyle(c).backgroundColor }; });
  ok(r && r.btn === 'rgb(37, 99, 235)' && r.card === 'rgb(255, 255, 255)', 'the Rate page\\'s buttons are the app\\'s blue and its cards the app\\'s white', r);"""),
])
