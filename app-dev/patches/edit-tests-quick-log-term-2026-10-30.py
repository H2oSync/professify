#!/usr/bin/env python3
"""Tests for quick-log-term-2026-10-30.py: the Builder's one tap now files the class under the most recent finished
term (Spring 2026 while Fall 2026 is the term people are in — the fixtures' config) because production refuses a
term-less class_history row; ✓ again deletes that dated row. pastClassSheet's term-less-row block now makes its
legacy term-less row directly (they still exist on accounts from before), since quickLog no longer writes one.
Usage: python3 edit-tests-quick-log-term-2026-10-30.py <repo-dir>   (replayable on a fresh checkout)"""
import sys, os
D = sys.argv[1] if len(sys.argv) > 1 else '.'
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""w[0].body.code === 'BUS 1100' && w[0].body.term === null && w[0].body.year === null && w[0].body.user_id === FX.ME.id && await page.locator('#sheet .tc-form').count() === 0, 'one tap: the class goes on your record with no term, and nothing opens', w);""",
    """w[0].body.code === 'BUS 1100' && w[0].body.term === 'Spring' && w[0].body.year === 2026 && w[0].body.user_id === FX.ME.id && await page.locator('#sheet .tc-form').count() === 0, 'one tap: the class goes on your record under the last finished term (Spring 2026 — production needs a term), and nothing opens', w);""", 'one tap post')
rep("""/term=is\\.null/.test(w[0].query) && /year=is\\.null/.test(w[0].query) && (await withLeft(page)).match(/(\\d+) filled\\s*(?:\\d+ in progress\\s*)?\\d+ left on your flowchart/)[1] === before, 'one tap: ✓ again undoes it — only the term-less record', w);""",
    """/term=eq\\.Spring/.test(w[0].query) && /year=eq\\.2026/.test(w[0].query) && (await withLeft(page)).match(/(\\d+) filled\\s*(?:\\d+ in progress\\s*)?\\d+ left on your flowchart/)[1] === before, 'one tap: ✓ again undoes it — only the one-tap’s own row', w);""", 'one tap delete')
rep("""w[1].body.code === 'MATH 1267' && w[1].body.term === null && chDone === 1""",
    """w[1].body.code === 'MATH 1267' && w[1].body.term === 'Spring' && w[1].body.year === 2026 && chDone === 1""", 'choice post')
rep("""  await page.evaluate(() => quickLog('BUS 1100', 'x')); await tick(page, 600);""",
    """  await page.evaluate(async () => { await TC.client().from('class_history').insert({ user_id: TC.user.id, code: 'BUS 1100', term: null, year: null, professor: null }); await TC.reloadHistory(); render(true); }); await tick(page, 600);   /* a term-less row from before 2026-10-30 */""", 'pastClassSheet setup')
open(P, 'w', encoding='utf-8').write(S); print('edit-tests-quick-log-term applied')
