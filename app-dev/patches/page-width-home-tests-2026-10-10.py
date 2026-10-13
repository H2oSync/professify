#!/usr/bin/env python3
"""check-app.mjs: the pageWidthHome test from build 2026-10-10 08:30 (the other session added it to its check-app by
hand; its folder had no tests script). Inserted verbatim before tests.planColors. Replayable.
Usage: python3 page-width-home-tests-2026-10-10.py app-dev/tests/check-app.mjs"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
BLOCK = r'''/* Page width on every tab (Tate, 2026-10-10): Explore, Rate, Planner, Past classes and Friends sit 12px from
   the screen edge, exactly like Home. Titles and small section labels stay at 16px (Home's section titles
   are 12+4 too), and the Schedule tab row keeps 16. */
tests.pageWidthHome = async () => {
  for (const w of [390, 320]) {
    const { page, close } = await openApp({ width: w });
    await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
    const edges = (screen, setup, sel) => page.evaluate(([setup, sel]) => { (0, eval)(setup); render(true); return null; }, [setup, sel]).then(async () => {
      await page.waitForTimeout(setup.includes('planner') ? 2600 : 700); if (setup.includes('planner')) { await page.evaluate(() => render(true)); await page.waitForTimeout(700); }
      return page.evaluate(sel => { const sr = document.getElementById('scroll').getBoundingClientRect(), o = {};
        for (const [k, s] of Object.entries(sel)) o[k] = [...document.querySelectorAll('#scroll ' + s)].filter(e => e.getClientRects().length).map(e => { const r = e.getBoundingClientRect(); const pd = /^\.(title|pl-top|pl-sech|fs-h|fs-note)$/.test(s) ? parseFloat(getComputedStyle(e).paddingLeft) : 0; return [Math.round(r.left - sr.left + pd), Math.round(sr.right - r.right)]; }); return o; }, sel); });
    const at = (m, k, v) => m[k].length > 0 && m[k].every(([l, r]) => l === v && r === v);
    const ex = await edges('ex', "S.tab='explore';S.exMode='classes'", { title: '.title', search: '.search', seg: '.seg', chips: '.fchip', cards: '.ccard' });
    ok(at(ex, 'search', 12) && at(ex, 'seg', 12) && at(ex, 'cards', 12) && ex.chips[0][0] === 12 && ex.title[0][0] === 16, `page width ${w}: Explore classes — search, tabs, chips and cards 12px from the edge, the title 16`, ex);
    const ep = await edges('ep', "S.tab='explore';S.exMode='profs'", { search: '.search', seg: '.seg', cards: '.pcard' });
    ok(at(ep, 'search', 12) && at(ep, 'seg', 12) && at(ep, 'cards', 12), `page width ${w}: Explore professors — search, tabs and cards 12px from the edge`, ep);
    const ra = await edges('ra', "S.tab='rate'", { title: '.title', cards: '.card.list' });
    ok(at(ra, 'cards', 12) && ra.title[0][0] === 16, `page width ${w}: Rate — the lists are 12px from the edge, the title 16`, ra);
    const fr = await edges('fr', "S.tab='friends'", { title: '.title', lab: '.fs-h', search: '.fsearch', lists: '.card.list', threads: '.thread' });
    ok(at(fr, 'search', 12) && at(fr, 'lists', 12) && at(fr, 'threads', 12) && fr.title[0][0] === 16 && fr.lab.length > 0 && fr.lab.every(([l]) => l === 16), `page width ${w}: Friends — search, requests, chats and friends 12px from the edge, the title 16`, fr);
    const pl = await edges('pl', "S.tab='schedule';S.schedTab='planner';localStorage.setItem(plSkipKey(),'1');TC.prefs={priority:'degree',units:16}", { plan: '.pl-card', picks: '.pl-picks', pk: '.pk-card', top: '.pl-top', sech: '.pl-sech' });
    ok(at(pl, 'plan', 12) && at(pl, 'picks', 12) && at(pl, 'pk', 12) && pl.top[0][0] === 16 && pl.sech[0][0] === 16, `page width ${w}: Planner — the plan card and the picks are 12px from the edge, the headings 16`, pl);
    const inj = await edges('inj', "S.tab='schedule';S.schedTab='planner'", { x: '.pl-card' }).then(() => page.evaluate(() => { const h = document.querySelector('#scroll .w12'); h.insertAdjacentHTML('beforeend', '<div class="pl-done" id="t-done">x</div><div class="pk-empty" id="t-empty">x</div>'); const sr = document.getElementById('scroll').getBoundingClientRect(); return ['t-done', 't-empty'].map(i => { const r = document.getElementById(i).getBoundingClientRect(); return [Math.round(r.left - sr.left), Math.round(sr.right - r.right)]; }); }));
    ok(inj.every(([l, r]) => l === 12 && r === 12), `page width ${w}: the Planner’s "all filled" card and its empty note are 12px from the edge`, inj);
    const fn = await edges('fn', "S.tab='friends';S.fq='a'", { note: '.fs-note' }); ok(fn.note.length > 0 && fn.note.every(([l]) => l === 16), `page width ${w}: the Friends search hint lines up with the labels`, fn);
    const pa = await edges('pa', "S.tab='schedule';S.schedTab='past'", { sec: '.tc-sec' });
    ok(at(pa, 'sec', 12), `page width ${w}: Past classes — the cards are 12px from the edge`, pa);
    const mi = await edges('mi', "S.tab='schedule';S.schedTab='mine'", { title: '.title', terms: '.seg.terms', cards: '.ccard' });
    ok(at(mi, 'terms', 12) && at(mi, 'cards', 12) && mi.title[0][0] === 16, `page width ${w}: My Classes is unchanged (cards 12, title 16)`, mi);
    const sw = await page.evaluate(() => { const s = document.getElementById('scroll'); return s.scrollWidth - s.clientWidth; });
    ok(sw <= 0, `page width ${w}: nothing scrolls sideways`, sw);
    if (w === 390) { const ho = await edges('ho', "S.tab='home'", { cards: '.hfeed .fcard' }); ok(at(ho, 'cards', 12), 'page width: Home is unchanged', ho); }
    await close();
  }
};
'''
if 'tests.pageWidthHome = async' in s: sys.exit('page-width-home-tests: already there')
a = 'tests.planColors = async () => {'
if s.count(a) != 1: sys.exit('page-width-home-tests: anchor')
s = s.replace(a, BLOCK + '\n' + a)
open(p, 'w', encoding='utf-8').write(s)
print('pageWidthHome added')
