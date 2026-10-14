/* check-dpr-synth-web — the same 300 synthetic Degree Progress Reports (files/make-dpr-corpus.py) through the WEBSITE's
   reader (index.html: pdfToText → dprParse → auditLines), each against the generator's answer key. Reader layer only.
     APP_DIR=<repo> node check-dpr-synth-web.mjs [dir] [--only synth-012] [--json out.json]
   Until the website carries reader v2 (an `audit` on dprParse's result) the requirement-line checks report 'no audit'.
   (2026-10-14, website-report-flow) 'Report read counts' runs on the website too: auditLines(a, null), the count the review
   list and Past classes show — a website without auditLines is a finding, not a skip.
   (2026-10-14, the website's half of check-dpr-synth)
   -- the original header follows --
   check-dpr-synth — the 300 synthetic Degree Progress Reports (since 2026-10-12 also Summer terms, minors, second
   majors, Incompletes and semester students past the first term, each read on its own printing day) (files/make-dpr-corpus.py) through the REAL phone app,
   each against the answer key the generator worked out from what its invented student actually did.
     node check-dpr-synth.mjs [dir] [--flow] [--only synth-012,synth-040] [--workers 4] [--json out.json]
   dir defaults to $DPR_SYNTH or /tmp/claude-0/dpr-synth (generated there first if empty).
   Without --flow: the reader only (every report, one page — about a minute).
   With --flow: every report through the whole app too — upload → Report read → save → Past classes → the Builder →
   reload — on a fresh account per report (the major from the report), in parallel pages. */
import { openApp } from './app-harness.mjs';
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const FLOW = false, only = (opt('--only', '') || '').split(',').filter(Boolean), workers = +opt('--workers', 4);
const dir = args.find((a, i) => !a.startsWith('--') && !['--only', '--workers', '--json'].includes(args[i - 1])) || process.env.DPR_SYNTH || '/tmp/claude-0/dpr-synth';
const here = path.dirname(new URL(import.meta.url).pathname);
if (!fs.existsSync(dir) || !fs.readdirSync(dir).some(f => /^synth-\d+\.pdf$/.test(f))) {
  console.log('generating the reports in', dir);
  execFileSync('python3', [path.join(here, 'files', 'make-dpr-corpus.py'), dir], { stdio: 'inherit' });
}
let ids = fs.readdirSync(dir).filter(f => /^synth-\d+\.pdf$/.test(f)).map(f => f.replace(/\.pdf$/, '')).sort();
if (only.length) ids = ids.filter(i => only.includes(i));
const keyOf = id => JSON.parse(fs.readFileSync(path.join(dir, id + '.key.json'), 'utf8'));
const results = {};
const add = (id, layer, what, detail) => { (results[id] = results[id] || []).push({ layer, what, detail }); };

/* ---------------------------------------------------------------- layer 1: the reader, every report */
async function readerPass() {
  /* a fresh account: no classes of its own (My Classes would cover open lines — that's the flow's business) */
  const FX = await import('./app-fixtures.mjs');
  const T = JSON.parse(JSON.stringify(FX.TABLES)); for (const t of ['class_history', 'my_sections', 'saved_classes', 'degree_audit', 'plans']) if (Array.isArray(T[t])) T[t] = T[t].filter(r => r.user_id !== FX.ME.id);
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 8198), tables: T, path: '/', width: 1440, height: 900, wait: 4000, terms: 'live' });
  await page.waitForFunction(() => typeof dprParse === 'function' && typeof pdfToText === 'function', null, { timeout: 15000 });
  for (const id of ids) {
    const K = keyOf(id);
    const want = [...new Set(Object.values(K.lines).flatMap(k => k.options.concat(k.used.map(e => e.n).filter(Boolean))))];
    /* the website's reader files rows by the terms it is configured with (website-spring-wall): read each report with the
       terms the app would ship on its printing day, as the phone's flow layer does */
    const ck = K.clock || { nowy: 2026, jan: (K.scenarios || []).some(t => /January/.test(t)) };
    const r = await page.evaluate(async ([b64, want, CFG]) => {
      Object.assign(window.PROFESSIFY_CONFIG, CFG);
      const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      const text = await pdfToText(new File([bytes], 'report.pdf', { type: 'application/pdf' }));
      const p = dprParse(text), a = p.audit || {}, R = p.rows || [];
      const X = (a && a.ok && typeof auditLines === 'function') ? auditLines(a, null) : null;
      return { ok: !!p.ok, aok: !!(a && a.ok), err: a && a.err, catalog: p.program && p.program.catalog, rows: R.length,
        xfer: R.filter(x => x._xfer).map(x => x.code + '|' + x.term + ' ' + x.year), taking: [...new Set(R.filter(x => x._now || x._reg).map(x => x.cur))].sort(),
        reqs: (a.reqs || []).map(b => ({ code: b.code, status: b.status, label: b.label, kind: b.kind, used: b.used, listed: b.listed, options: b.options })),
        counts: X ? { filled: X.filled.length, left: X.open.length, unknown: X.unknown.length } : null,
        units: [a.units_used, a.units_needed, a.units_required], kept: JSON.stringify({ a, prog: p.program }),
        canon: Object.fromEntries(want.map(c => [c, (typeof canonCode === 'function' && canonCode(c)) || c])) };
    }, [fs.readFileSync(path.join(dir, id + '.pdf')).toString('base64'), want, termsFor(ck.nowy)]);
    const cn = c => (c && r.canon[c]) || c;
    if (!r.ok) { add(id, 'reader', 'not read', r.err || ''); continue; }
    if (!r.aok) { add(id, 'reader', 'no audit (reader v2 missing)', r.err || ''); }
    if (r.catalog !== K.catalog) add(id, 'reader', 'catalog', `${r.catalog} ≠ ${K.catalog}`);
    if (r.rows !== K.read.rows) add(id, 'reader', 'Course History rows', `${r.rows} ≠ ${K.read.rows}`);
    if (JSON.stringify(r.taking) !== JSON.stringify(K.read.taking)) add(id, 'reader', 'classes being taken', { missing: K.read.taking.filter(c => !r.taking.includes(c)), extra: r.taking.filter(c => !K.read.taking.includes(c)) });
    if (K.icons && r.xfer.length !== K.read.transfer) add(id, 'reader', 'transfer rows', `${r.xfer.length} ≠ ${K.read.transfer}: ${r.xfer.join(', ')}`);
    const U = K.read.units;
    if (JSON.stringify(r.units) !== JSON.stringify(U)) add(id, 'reader', 'total units', `${JSON.stringify(r.units)} ≠ ${JSON.stringify(U)}`);
    /* every line the key printed, read with the right verdict and the classes the report used */
    if (!r.aok) continue;
    const byCode = new Map(r.reqs.map(b => [b.code, b]));
    /* the app writes a requirement's code the 2022 way: (R2801) is R-2801 */
    K.lines = Object.fromEntries(Object.entries(K.lines).map(([c, v]) => [c.replace(/^R(\d+)$/, 'R-$1'), v]));
    for (const [code, k] of Object.entries(K.lines)) {
      const b = byCode.get(code);
      if (!b) { add(id, 'reader', 'line missing', `${code} (${k.kind}, ${k.read})`); continue; }
      const want = k.read === 'need' ? ['not'] : k.read === 'unknown' ? ['unknown'] : ['satisfied', 'in_progress'];
      if (!want.includes(b.status)) add(id, 'reader', 'line status', `${code} ${k.kind} "${b.label}": read ${b.status}, key ${k.read} (printed ${k.printed})`);
      const got = new Set((b.used || []).map(e => e.c + '|' + e.t)), exp = new Set(k.used.map(e => e.c + '|' + e.t));
      if ([...exp].some(x => !got.has(x)) || [...got].some(x => !exp.has(x))) add(id, 'reader', 'line classes', `${code}: read [${[...got]}] key [${[...exp]}]`);
      for (const e of k.used) { const g = (b.used || []).find(x => x.c === e.c && x.t === e.t); if (!g) continue;
        if (cn(g.n || null) !== cn(e.n || null) && !(e.n === null && g.n === undefined)) add(id, 'reader', 'today’s number', `${code} ${e.c}: read ${g.n} key ${e.n}`);
        if (K.icons && !!g.x !== !!e.x) add(id, 'reader', 'transfer flag on a line’s class', `${code} ${e.c}: read ${!!g.x} key ${e.x}`); }
      if (k.dminc && k.kind === 'major' && !(b.listed || []).some(c => c === k.dminc || c === cn(k.dminc))) add(id, 'reader', 'a D the report didn’t count not flagged', `${code}: listed [${b.listed}] key ${k.dminc}`);
      if (/^(major|choice)$/.test(k.kind) && k.options.length && b.options && !k.options.every(c => b.options.includes(cn(c)) || b.options.includes(c))) add(id, 'reader', 'line options', `${code}: read [${b.options}] key [${k.options}]`);
    }
    for (const b of r.reqs) if (!K.lines[b.code]) add(id, 'reader', 'extra line', `${b.code} ${b.kind} "${b.label}" ${b.status}`);
    if (!r.counts) add(id, 'reader', 'Report read counts', 'auditLines missing on the website');
    else if (r.counts.filled !== K.read.filled || r.counts.left !== K.read.left || r.counts.unknown !== K.read.unknown) add(id, 'reader', 'Report read counts', `${JSON.stringify(r.counts)} ≠ ${JSON.stringify({ filled: K.read.filled, left: K.read.left, unknown: K.read.unknown })}`);
    /* nothing personal kept */
    const leak = K.secret.filter(x => r.kept.includes(x)).concat(K.secret[0].split(' ').filter(w => w.length > 3 && new RegExp('\\b' + w + '\\b').test(r.kept)));
    if (leak.length || /(^|[^\d])98\d{5}([^\d]|$)/.test(r.kept) || /(?:^|\s)(?:[A-DF][+-]?|CR|NC|W)\s+\d+\.\d{2}\b/.test(r.kept)) add(id, 'reader', 'PERSONAL DATA KEPT', leak);
  }
  await close();
}


const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
function termsFor(y) {
  if (y === 2026) return SPRING_CFG;
  const f = '2' + String(y).slice(2) + '8', sp = '2' + String(y + 1).slice(2) + '4';
  return { TERM: sp, TERM_LABEL: 'Spring ' + (y + 1), NOW_TERM: f, NOW_LABEL: 'Fall ' + y, NOW_UNTIL: (y + 1) + '-01-25' };
}
const t0 = Date.now();
await readerPass();
console.log(`reader (website): ${ids.length} reports in ${Math.round((Date.now() - t0) / 1000)}s`);
const byWhat = {};
for (const [id, fs_] of Object.entries(results)) for (const f of fs_) (byWhat[f.layer + ': ' + f.what] = byWhat[f.layer + ': ' + f.what] || []).push(id);
const clean = ids.filter(id => !results[id]);
console.log(`\n${clean.length} of ${ids.length} reports with no finding`);
for (const [w, list] of Object.entries(byWhat).sort((a, b) => b[1].length - a[1].length)) console.log(`  ${String(new Set(list).size).padStart(3)} reports · ${w}   e.g. ${[...new Set(list)].slice(0, 3).join(', ')}`);
const out = opt('--json', '');
if (out) fs.writeFileSync(out, JSON.stringify(results, null, 1));
process.exit(clean.length === ids.length ? 0 : 1);
