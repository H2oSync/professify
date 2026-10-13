#!/usr/bin/env python3
"""check-app.mjs + mutate.mjs edits for Planner card A's plain day off (2026-10-10). Replayable.
  python3 edit-tests-day-off-plain-2026-10-10.py"""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, 'check-app.mjs'); L = open(P, encoding='utf-8').read().split('\n')

def swap(find, new):
    hits = [i for i, l in enumerate(L) if find in l]
    if len(hits) != 1: sys.exit(f'edit-tests-day-off: "{find[:60]}" found {len(hits)}x (want 1)')
    L[hits[0]] = new

swap("      free: [...c.querySelectorAll('.pla-dh span.free')].map(e => e.textContent), freeCols: c.querySelectorAll('.pla-free').length,",
     "      cols: [...c.querySelectorAll('.pla-cols > .pla-col')].map(e => [e.querySelectorAll('.pla-blk').length, e.innerText.trim(), getComputedStyle(e).backgroundColor]), dh: [...c.querySelectorAll('.pla-dh span')].map(e => [e.textContent, e.className, getComputedStyle(e).color]),")
swap("  ok(a.freeCols === a.free.length && a.free.length === a.off.length, 'card A: a weekday with no class says Free', { free: a.free, off: a.off });",
     "  const offCols = a.cols.filter((x, i) => a.off.includes('MTWRF'[i]));\n"
     "  ok(a.cols.length === 5 && a.off.length >= 1 && offCols.length === a.off.length && offCols.every(x => x[0] === 0 && x[1] === '' && x[2] === a.cols.find(y => y[0])[2]) && new Set(a.dh.map(x => x[2])).size === 1 && a.dh.every(x => !x[1]) && !/\\bfree\\b/i.test(a.text), 'card A: a day off is a plain column like the others (Tate: “take out the free friday make it normal”)', { cols: a.cols, dh: a.dh, off: a.off });")
open(P, 'w', encoding='utf-8').write('\n'.join(L))

M = os.path.join(H, 'mutate.mjs'); s = open(M, encoding='utf-8').read()
old = '  ["card A: a free weekday says nothing", "if (!day.length) return `<div class=\\"pla-col pla-free\\"><span>Free</span></div>`;", "if (!day.length) return `<div class=\\"pla-col\\"></div>`;", "springCardA"],\n'
new = ('  ["card A: the day off says Free again", "if (!day.length) return `<div class=\\"pla-col\\"></div>`;", "if (!day.length) return `<div class=\\"pla-col\\"><span>Free</span></div>`;", "springCardA"],\n'
       '  ["card A: the day off painted green again", "if (!day.length) return `<div class=\\"pla-col\\"></div>`;", "if (!day.length) return `<div class=\\"pla-col\\" style=\\"background:var(--green-wash)\\"></div>`;", "springCardA"],\n'
       '  ["card A: the day off\'s name marked again", "${PL_DAYS.map(([d, nm]) => `<span>${nm}</span>`).join(\'\')}", "${PL_DAYS.map(([d, nm]) => `<span class=\\"${timed.some(x => x.days.includes(d)) ? \'\' : \'free\'}\\" style=\\"${timed.some(x => x.days.includes(d)) ? \'\' : \'color:var(--green-ink3)\'}\\">${nm}</span>`).join(\'\')}", "springCardA"],\n')
if old in s: s = s.replace(old, new)
elif new not in s: sys.exit('edit-tests-day-off: mutant missing')
open(M, 'w', encoding='utf-8').write(s)
print('edit-tests-day-off-plain: done')
