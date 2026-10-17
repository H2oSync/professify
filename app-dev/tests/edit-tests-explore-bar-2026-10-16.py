#!/usr/bin/env python3
"""(2026-10-16) Keeps the older desktop checks true after explore-bar-2026-10-16.py (website; marker 'explore-bar (2026-10-16)'):
  check-desktop-explore-term.mjs  Explore's term control is ONE switch button (#exContext .ex-termsw, data-term spring|now) after the text tabs, not two
                                  .ex-term pills inside the filter group;
  check-desktop-terms.mjs         Schedule > My classes: the term is ONE switch button (#watchMineOut > .mc-terms .mc-termsw), not two pills.
Usage: python3 edit-tests-explore-bar-2026-10-16.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
def edit(name, pairs):
    p = root / 'app-dev/tests' / name; s = p.read_text()
    if 'explore-bar (2026-10-16)' in s: sys.exit('already edited ' + name)
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:100]); s = s.replace(a, b)
    s = s.rstrip('\n') + '\n/* explore-bar (2026-10-16): this file was updated by edit-tests-explore-bar-2026-10-16.py */\n'
    p.write_text(s); print('edited', p)

edit('check-desktop-explore-term.mjs', [
 ("""const clickTerm = (page, t) => page.evaluate(t => document.querySelector('#exContext .ex-term[data-term="' + t + '"]').click(), t);""",
  """/* explore-bar: the term is ONE switch button showing the current term; it flips, so click only when it is not already on t */
const clickTerm = (page, t) => page.evaluate(t => { const b = document.querySelector('#exContext .ex-termsw'); if (b.getAttribute('data-term') !== t) b.click(); }, t);"""),
 ("""ok((await page.$$('#exContext .ex-term')).length === 0, 'single term: no term switch in Explore');""",
  """ok((await page.$$('#exContext .ex-termsw')).length === 0, 'single term: no term switch in Explore');"""),
 ("""const sw = () => page.evaluate(() => [...document.querySelectorAll('#exContext .ex-term')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')).join('|'));""",
  """const sw = () => page.evaluate(() => [...document.querySelectorAll('#exContext .ex-termsw')].map(b => b.textContent.trim() + '*').join('|'));"""),
 ("""ok(await sw() === 'Spring 2027*|Fall 2026', 'switch: Spring 2027 | Fall 2026, starting on Spring', await sw());""",
  """ok(await sw() === 'Spring 2027*', 'switch: ONE switch (not two pills), starting on Spring 2027', await sw());"""),
 ("""ok(await sw() === 'Spring 2027|Fall 2026*', 'switch: Fall 2026 is now lit', await sw());""",
  """ok(await sw() === 'Fall 2026*', 'switch: one tap flips it to Fall 2026', await sw());"""),
])
edit('check-desktop-terms.mjs', [
 ("""  let mc = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#watchMineOut > .mc-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')),""",
  """  let mc = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#watchMineOut > .mc-terms button')].map(b => b.textContent.trim() + '*'),"""),
 ("""  mc = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#watchMineOut > .mc-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')),""",
  """  mc = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#watchMineOut > .mc-terms button')].map(b => b.textContent.trim() + '*'),"""),
 ("""ok(mc.chips.join('|') === 'Fall 2026|Spring 2027*' && mc.add""", """ok(mc.chips.join('|') === 'Spring 2027*' && mc.add"""),
 ("""ok(mc.chips.join('|') === 'Fall 2026*|Spring 2027' && !mc.add""", """ok(mc.chips.join('|') === 'Fall 2026*' && !mc.add"""),
 ("""'my classes: Fall 2026 · Spring 2027, open on Spring — the list you add to'""", """'my classes: one term switch (not two pills), open on Spring 2027 — the list you add to'"""),
])
