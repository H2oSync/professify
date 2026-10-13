#!/usr/bin/env python3
"""Test for dpr-short-ge-heads-2026-10-11.py. Run AFTER edit-tests-past-left-builder-top-2026-10-11.py.
Usage: python3 edit-tests-dpr-short-ge-heads-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
if 'tests.dprShortGeHeads' not in S:
    a = "\nconst names = Object.keys(tests).filter(n => !only || n === only);"
    if S.count(a) != 1: sys.exit('short ge heads: anchor')
    S = S.replace(a, r"""
/* (2026-10-11) A friend's real report prints each GE line under a short heading ("B2", "C Elect LD", "F (ES)", "GE Elect:
   Elective in Area B/c/d") over the verdict that names it. The synthetic reports, given the same short headings, must read
   exactly as without them: the same names, the same GE areas. */
tests.dprShortGeHeads = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  for (const f of ['dpr-stress-quarter.pdf', 'dpr-stress-mixed.pdf']) {
    const r = await page.evaluate(async b64 => {
      const lib = await loadPdfJs(); const doc = await lib.getDocument({ data: Uint8Array.from(atob(b64), c => c.charCodeAt(0)), isOffscreenCanvasSupported: false }).promise; const t = await dprDocText(doc); doc.destroy();
      let n = 0;
      const t2 = t.split('\n').map(l => {
        const m = /^(?:Not Satisfied|Satisfied|In Progress):\s*((?:[A-F](?:[1-5]| ?UD)?|[1-6][A-C]?))(?:\s*\(Qtr\))?:\s/.exec(l);
        if (m) { n++; return m[1] + '\n' + l; }
        if (/^(?:Not Satisfied|Satisfied|In Progress):\s*LOWER-DIVISION C ELECTIVE\b/i.test(l)) { n++; return 'C Elect LD\n' + l; }
        if (/^(?:Not Satisfied|Satisfied|In Progress):\s*GE Elective:/i.test(l)) { n++; return 'GE Elect: Elective in Area B/c/d\n' + l; }
        return l;
      }).join('\n');
      plSync();
      const ge = p => p.audit.reqs.filter(b => b.kind === 'ge').map(b => [b.label, b.ge || '', plGeArea(b).join('/'), b.status].join(' | '));
      return { n, a: ge(TCPL.dprParse(t)), b: ge(TCPL.dprParse(t2)) };
    }, nodeFs.readFileSync(nodePath.join('files', f)).toString('base64'));
    ok(r.n >= 8 && r.a.length >= 8 && JSON.stringify(r.b) === JSON.stringify(r.a), `reader (${f}): GE lines under short headings (“B2”, “C Elect LD”, “GE Elect: …”) read with the verdict’s name and their GE area`, { n: r.n, diff: r.b.filter(x => !r.a.includes(x)).slice(0, 6) });
  }
  ok(log.errors.length === 0, 'short GE headings: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""")
    open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
PL = open(os.path.join(D, 'app', 'planner.js'), encoding='utf-8').read()
MUT = [("reader: short GE heading kept", "        if(head&&words&&!courseLine){ var wl=dprTidyLabel(words);", "        if(false){ var wl=dprTidyLabel(words);", "dprShortGeHeads", "planner")]
for n, a, b, t, g in MUT:
    if PL.count(a) != 1: sys.exit(f'mutant anchor {n}: {PL.count(a)}x')
if 'edit-tests-dpr-short-ge-heads-2026-10-11.py' not in T:
    k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
    T = T.replace(k, "\n  /* the reader: GE lines under short headings (2026-10-11; edit-tests-dpr-short-ge-heads-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-dpr-short-ge-heads: done')
