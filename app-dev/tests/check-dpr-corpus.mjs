/* check-dpr-corpus — real Degree Progress Reports through the REAL phone app's reader, each against a hand-checked
   answer key. The reports and their keys NEVER go in the repo: they live in a folder on your own computer.
     node check-dpr-corpus.mjs [folder] [--write-keys]
   folder defaults to $DPR_CORPUS, else ~/Downloads/TermChamp DPR test reports. For each <name>.pdf there:
     <name>.key.json  { "counts": {satisfied, not, in_progress, unknown}, "open": ["…line words…"], "units": [used, needed, required],
                        "transfer": ["SUBJ NNNN", …], "taking": ["SUBJ NNNN", …] }   (the last two optional: the classes the
                        reader calls transfer/test credit, and the ungraded classes in the newest term — by the codes the app saves)
   --write-keys writes a key for every PDF that has none, from what the reader reads now — CHECK IT BY HAND
   against the PDF before trusting it (the open lines are the report's "Not Satisfied:" lines).
   Every run also checks that nothing personal survives the read: the report's own name and ID lines are found
   by pattern, kept in memory, never printed, and must not appear in anything the reader kept.
   Needs app-dev/out/ built (the harness serves the app from there) and Playwright, like check-app. */
import { openApp } from './app-harness.mjs';
import fs from 'node:fs'; import path from 'node:path'; import os from 'node:os';
const args = process.argv.slice(2), write = args.includes('--write-keys');
const dir = args.find(a => !a.startsWith('--')) || process.env.DPR_CORPUS || path.join(os.homedir(), 'Downloads', 'TermChamp DPR test reports');
if (!fs.existsSync(dir)) { console.log('No folder:', dir); process.exit(1); }
const pdfs = fs.readdirSync(dir).filter(f => /\.pdf$/i.test(f)).sort();
if (!pdfs.length) { console.log('No PDFs in', dir); process.exit(1); }
const { page, close } = await openApp({ port: +(process.env.APP_PORT || 8196) });
await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
let bad = 0;
for (const f of pdfs) {
  const name = f.replace(/\.pdf$/i, ''), keyFile = path.join(dir, name + '.key.json');
  const r = await page.evaluate(async b64 => {
    const lib = await loadPdfJs(); const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    /* exactly as the app reads it (readDpr): the text and the report's transfer icon */
    const doc = await lib.getDocument({ data: bytes, isOffscreenCanvasSupported: false }).promise; const text = await dprDocText(doc);
    const parsed = TCPL.dprParse(text), a = parsed.audit || {}, R = parsed.rows || [];
    return { text, ok: !!parsed.ok, rows: R.length, program: parsed.program || null, audit: a,
      transfer: [...new Set(R.filter(x => x._xfer).map(x => x.cur))].sort(), taking: [...new Set(R.filter(x => x._now).map(x => x.cur))].sort(),
      open: (a.reqs || []).filter(b => b.status === 'not').map(b => b.label), units: [a.units_used, a.units_needed, a.units_required] };
  }, fs.readFileSync(path.join(dir, f)).toString('base64'));
  const secret = [];
  for (const re of [/Name\s*:\s*([^\n]+?)\s*(?:EMPLID|$)/m, /^For\s+([^\n]+)$/m]) { const m = re.exec(r.text); if (m) secret.push(m[1].trim()); }
  const id = /EMPLID\s*:\s*(\d{5,})/.exec(r.text); if (id) secret.push(id[1]);
  secret.slice().forEach(s => s.split(/[\s,]+/).filter(w => w.length >= 3 && /^[A-Za-z'-]+$/.test(w)).forEach(w => secret.push(w)));
  const kept = JSON.stringify({ audit: r.audit, program: r.program });
  const leak = secret.filter(s => kept.includes(s)).length + (/\d{7}/.test(kept) ? 1 : 0) + (/(^|\s)([A-DF][+-]?|CR|NC)\s+\d+\.\d{2}\b/.test(kept) ? 1 : 0);
  const got = { counts: (r.audit && r.audit.counts) || null, open: r.open.slice().sort(), units: r.units, transfer: r.transfer, taking: r.taking };
  let verdict;
  if (!r.ok || !r.audit || !r.audit.ok) verdict = 'NOT READ';
  else if (!fs.existsSync(keyFile)) { if (write) { fs.writeFileSync(keyFile, JSON.stringify(got, null, 1)); verdict = 'key written — check it by hand'; } else verdict = 'no key (run with --write-keys)'; }
  else {
    const key = JSON.parse(fs.readFileSync(keyFile, 'utf8')), diff = [];
    if (JSON.stringify(key.counts) !== JSON.stringify(got.counts)) diff.push(`counts ${JSON.stringify(got.counts)} ≠ key ${JSON.stringify(key.counts)}`);
    const ko = (key.open || []).slice().sort();
    if (JSON.stringify(ko) !== JSON.stringify(got.open)) diff.push(`open lines: missing [${ko.filter(x => !got.open.includes(x)).join(' | ')}], extra [${got.open.filter(x => !ko.includes(x)).join(' | ')}]`);
    if (key.units && JSON.stringify(key.units) !== JSON.stringify(got.units)) diff.push(`units ${JSON.stringify(got.units)} ≠ key ${JSON.stringify(key.units)}`);
    for (const f of ['transfer', 'taking']) if (key[f]) { const k = key[f].slice().sort(); if (JSON.stringify(k) !== JSON.stringify(got[f])) diff.push(`${f}: missing [${k.filter(x => !got[f].includes(x)).join(', ')}], extra [${got[f].filter(x => !k.includes(x)).join(', ')}]`); }
    verdict = diff.length ? 'MISMATCH — ' + diff.join(' · ') : 'matches its key';
  }
  if (leak || /^(NOT READ|MISMATCH)/.test(verdict)) bad++;
  console.log(`${f}: ${r.rows} classes · ${got.transfer.length} transfer · ${got.taking.length} taking · ${JSON.stringify(got.counts)} · ${got.open.length} open · ${verdict}${leak ? ' · PERSONAL DATA KEPT ×' + leak : ' · nothing personal kept'}`);
}
await close();
console.log(`\n${pdfs.length - bad} of ${pdfs.length} reports read right`);
process.exit(bad ? 1 : 0);
