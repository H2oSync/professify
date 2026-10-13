#!/usr/bin/env python3
"""Tests for builder-foot-2026-10-13.py: the card's foot is two text links of one size. Replayable.
  python3 edit-tests-builder-foot-2026-10-13.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)
edit('check-app.mjs', [
("""    ok(q.opts.length > 3 && q.more === 'Show top 3', 'builder: See all N lists every option, and offers Show top 3', { n: q.opts.length, more: q.more });""",
 """    ok(q.opts.length > 3 && q.more === 'See less', 'builder: See more lists every option, and offers See less', { n: q.opts.length, more: q.more });""", 'left'),
("""sp2.more === 'See all 4' && sp2.mark""", """sp2.more === 'See more' && sp2.mark""", 'sp2'),
("""'options: Senior Project opens down to its top three, See all 4, Mark done'""", """'options: Senior Project opens down to its top three, See more, Mark done'""", 'sp2 words'),
("""  ok(v.cards[1].opts.length === 4 && v.cards[1].more === 'Show top 3', 'options: See all lists every one, then Show top 3', [v.cards[1].opts.length, v.cards[1].more]);""",
 """  ok(v.cards[1].opts.length === 4 && v.cards[1].more === 'See less', 'options: See more lists every one, then See less (Tate, 2026-10-13)', [v.cards[1].opts.length, v.cards[1].more]);""", 'more'),
("""  ok(v.cards[1].opts.length === 4 && v.cards[1].more === 'See less', 'options: See more lists every one, then See less (Tate, 2026-10-13)', [v.cards[1].opts.length, v.cards[1].more]);""",
 """  ok(v.cards[1].opts.length === 4 && v.cards[1].more === 'See less', 'options: See more lists every one, then See less (Tate, 2026-10-13)', [v.cards[1].opts.length, v.cards[1].more]);
  /* (2026-10-13) the foot: two text links of one size on one row — no pill (Tate: "rework how this looks") */
  const ft = await page.evaluate(() => { const f = document.querySelector('#scroll .plq-card:nth-child(2) .plq-foot'), m = f.querySelector('.plq-more'), k = f.querySelector('.plq-mark'), cm = getComputedStyle(m), ck = getComputedStyle(k);
    return { bg: cm.backgroundColor, size: [cm.fontSize, ck.fontSize], w: [cm.fontWeight, ck.fontWeight], chev: !!m.querySelector('svg'), exp: m.getAttribute('aria-expanded'), row: Math.abs(m.getBoundingClientRect().top - k.getBoundingClientRect().top) < 2, left: m.getBoundingClientRect().left < k.getBoundingClientRect().left, h: m.getBoundingClientRect().height }; });
  ok(/rgba\\(0, 0, 0, 0\\)|transparent/.test(ft.bg) && ft.size[0] === ft.size[1] && ft.w[0] === ft.w[1] && ft.chev && ft.exp === 'true' && ft.row && ft.left && ft.h >= 44, 'options: the foot is “See less ⌃” and “Mark done” as two plain links of one size on one row, 44px tall', ft);""", 'foot'),
])
MUT = r'''  ["foot: the pill back", ".plq-more,.plq-mark{display:inline-flex;align-items:center;gap:3px;min-height:44px;padding:0 2px;font-size:13.5px;font-weight:900;background:none;border-radius:0}", ".plq-more,.plq-mark{display:inline-flex;align-items:center;gap:3px;min-height:44px;padding:0 2px;font-size:13.5px;font-weight:900;border-radius:0}\n.plq-more{background:var(--tint1);flex:1;font-size:14px}", "builderOptions"],
  ["foot: no chevron on See more", "${all ? 'See less' : 'See more'}${ic('chevR', 12, 3)}</button>", "${all ? 'See less' : 'See more'}</button>", "builderOptions"],
  ["foot: See more never says See less", "${all ? 'See less' : 'See more'}${ic('chevR', 12, 3)}", "${all ? 'See more' : 'See more'}${ic('chevR', 12, 3)}", "builderOptions"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants')])
print('edit-tests-builder-foot: +1 check, 4 re-aimed, 3 mutants')
