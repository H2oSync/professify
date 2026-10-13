#!/usr/bin/env python3
"""Tests for filter-label-out-2026-10-11.py. Usage: python3 edit-tests-filter-label-out-2026-10-11.py <repo-dir>"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
a = """  ok(sb.t[0] === 'BUS' && sb.btn === 'Fall 2026', 'switch: with a subject chosen, the subject and the switch both show', sb);"""
b = """  const flNf = await page.evaluate(() => (document.querySelector('.fchip .n') || {}).textContent || '');
  ok(!sb.t.includes('BUS') && sb.btn === 'Fall 2026' && flNf === '1', 'switch: with a subject chosen, only the term shows beside Filters — the filter is the count on Filters (Tate, 2026-10-11)', { sb, flNf });
  await click(page, '[data-a="exMode"][data-x="profs"]');
  const flSp = await page.evaluate(() => [...document.querySelectorAll('.frow .muted.b')].map(e => e.textContent).join('|'));
  ok(flSp === 'Spring 2027', 'switch: Professors with a subject chosen shows only the term too', flSp);
  await click(page, '[data-a="exMode"][data-x="classes"]');"""
if S.count(a) != 1: sys.exit('anchor')
S = S.replace(a, b); a2 = """  ok(/GEs/.test(await page.locator('.frow').innerText()), 'filters: the bar says GEs');"""
b2 = """  ok(!/GEs/.test(await page.locator('.frow').innerText()) && (await page.locator('.frow .fchip .n').innerText()) === '1', 'filters: the bar shows the filter as the count on Filters, never the words (Tate, 2026-10-11)');"""
if S.count(a2) != 1: sys.exit('anchor GEs')
S = S.replace(a2, b2)
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
MUT = [("filter words: the subject shows beside Filters again", "  const subj = '';\n  if (!(S.exMode === 'classes' && splitTerms())) return `<span", "  const subj = S.subj !== 'All' ? `<span class=\"muted b\">${esc(subjLabel(S.subj))}</span>` : '';\n  if (!(S.exMode === 'classes' && splitTerms())) return subj || `<span", "exploreTerm", None)]
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit('mutant anchor ' + n)
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
T = T.replace(k, "\n  /* only the term beside Filters (2026-10-11; edit-tests-filter-label-out-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-filter-label-out: done')
