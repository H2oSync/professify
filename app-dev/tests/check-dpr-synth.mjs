/* check-dpr-synth — the 300 synthetic Degree Progress Reports (since 2026-10-12 also Summer terms, minors, second
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
const FLOW = args.includes('--flow'), only = (opt('--only', '') || '').split(',').filter(Boolean), workers = +opt('--workers', 4);
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
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 8196), tables: T });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  for (const id of ids) {
    const K = keyOf(id);
    const want = [...new Set(Object.values(K.lines).flatMap(k => k.options.concat(k.used.map(e => e.n).filter(Boolean))))];
    const r = await page.evaluate(async ([b64, want]) => {
      const lib = await loadPdfJs(); const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      const doc = await lib.getDocument({ data: bytes, isOffscreenCanvasSupported: false }).promise; const text = await dprDocText(doc);
      const p = TCPL.dprParse(text), a = p.audit || {}, R = p.rows || [];
      const X = a && a.ok ? auditLines(a, null) : null;
      return { ok: !!p.ok, aok: !!(a && a.ok), err: a && a.err, catalog: p.program && p.program.catalog, rows: R.length,
        xfer: R.filter(x => x._xfer).map(x => x.code + '|' + x.term + ' ' + x.year), taking: [...new Set(R.filter(x => x._now).map(x => x.cur))].sort(),
        reqs: (a.reqs || []).map(b => ({ code: b.code, status: b.status, label: b.label, kind: b.kind, used: b.used, listed: b.listed, options: b.options })),
        counts: X ? { filled: X.filled.length, left: X.open.length, unknown: X.unknown.length } : null,
        units: [a.units_used, a.units_needed, a.units_required], kept: JSON.stringify({ a, prog: p.program }),
        canon: Object.fromEntries(want.map(c => [c, TCPL.canon(c) || c])) };
    }, [fs.readFileSync(path.join(dir, id + '.pdf')).toString('base64'), want]);
    const cn = c => (c && r.canon[c]) || c;
    if (!r.ok || !r.aok) { add(id, 'reader', 'not read', r.err || ''); continue; }
    if (r.catalog !== K.catalog) add(id, 'reader', 'catalog', `${r.catalog} ≠ ${K.catalog}`);
    if (r.rows !== K.read.rows) add(id, 'reader', 'Course History rows', `${r.rows} ≠ ${K.read.rows}`);
    if (JSON.stringify(r.taking) !== JSON.stringify(K.read.taking)) add(id, 'reader', 'classes being taken', { missing: K.read.taking.filter(c => !r.taking.includes(c)), extra: r.taking.filter(c => !K.read.taking.includes(c)) });
    if (K.icons && r.xfer.length !== K.read.transfer) add(id, 'reader', 'transfer rows', `${r.xfer.length} ≠ ${K.read.transfer}: ${r.xfer.join(', ')}`);
    const U = K.read.units;
    if (JSON.stringify(r.units) !== JSON.stringify(U)) add(id, 'reader', 'total units', `${JSON.stringify(r.units)} ≠ ${JSON.stringify(U)}`);
    /* every line the key printed, read with the right verdict and the classes the report used */
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
    if (r.counts && (r.counts.filled !== K.read.filled || r.counts.left !== K.read.left || r.counts.unknown !== K.read.unknown)) add(id, 'reader', 'Report read counts', `${JSON.stringify(r.counts)} ≠ ${JSON.stringify({ filled: K.read.filled, left: K.read.left, unknown: K.read.unknown })}`);
    /* nothing personal kept */
    const leak = K.secret.filter(x => r.kept.includes(x)).concat(K.secret[0].split(' ').filter(w => w.length > 3 && new RegExp('\\b' + w + '\\b').test(r.kept)));
    if (leak.length || /(^|[^\d])98\d{5}([^\d]|$)/.test(r.kept) || /(?:^|\s)(?:[A-DF][+-]?|CR|NC|W)\s+\d+\.\d{2}\b/.test(r.kept)) add(id, 'reader', 'PERSONAL DATA KEPT', leak);
  }
  await close();
}

/* ---------------------------------------------------------------- layer 2: the whole flow, every report */
async function flowOne(id, port) {
  const K = keyOf(id);
  const major = K.flowchart ? K.major : K.major;
  /* the app's clock on the day the report was printed: a January report is read in January; (2026-10-12) a report printed
     a year or two later is read then, with the terms the app would ship that year */
  const ck = K.clock || { nowy: 2026, jan: (K.scenarios || []).some(t => /January/.test(t)) };
  const CFG = termsFor(ck.nowy);
  /* the terms (picking next Spring while this Fall is on), and a section in both for every class the report names —
     so the Builder has the whole catalog to pick from, and any wrong pick shows */
  const { page, close, log } = await openApp({ port, tables: synthTables(major, K.standing, K, CFG), height: 2600, terms: CFG, time: ck.jan ? `${ck.nowy + 1}-01-13T10:30:00-08:00` : `${ck.nowy}-10-09T10:30:00-07:00` });
  try {
    await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 12000 });
    await page.locator('[data-a="tab"][data-x="schedule"]').first().click(); await page.waitForTimeout(300);
    await page.locator('[data-a="schedTab"][data-x="planner"]').first().click(); await page.waitForTimeout(2500);
    const inp = page.locator('input[data-in="dprfile"]').first();
    if (!(await inp.count())) { add(id, 'flow', 'no upload button', ''); return; }
    await inp.setInputFiles(path.join(dir, id + '.pdf'));
    for (let i = 0; i < 40 && !(await page.locator('#sheet .dr-h1, #sheet .tc-err').count()); i++) await page.waitForTimeout(400);
    const err = await page.locator('#sheet .tc-err').count();
    if (err) { add(id, 'flow', 'Report read error', await page.locator('#sheet .tc-err').first().innerText()); return; }
    const pills = await page.evaluate(() => [...document.querySelectorAll('#sheet .dr-pill')].map(p => p.innerText.trim()));
    const want = [`${K.read.filled} filled`, `${K.read.left} left`].concat(K.read.unknown ? [`${K.read.unknown} can’t check`] : []);
    if (!want.every(w => pills.includes(w))) add(id, 'flow', 'Report read pills', `${pills.join(' | ')} — key ${want.join(' | ')}`);
    /* save */
    const save = page.locator('[data-a="dprSave"]');
    if (!(await save.count())) { add(id, 'flow', 'no save button', pills.join('|')); return; }
    await save.first().click(); await page.waitForTimeout(2600);
    await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; if (UI.sheet && /^(pcWho|dprDiff|wkAsk)$/.test(UI.sheet.type || '')) UI.sheet = null; render(true); });
    const posted = t => log.writes.filter(w => w.table === t && w.m === 'POST').map(w => w.body).flat();
    const hist = posted('class_history'), au = (log.writes.find(w => w.table === 'degree_audit' && w.m === 'POST') || {}).body;
    if (!au) add(id, 'flow', 'no report saved', '');
    const keptAll = JSON.stringify({ hist, au });
    if (K.secret.some(x => keptAll.includes(x)) || /(?:^|[\s"])(?:[A-DF][+-]?|CR|NC)\s+\d+\.\d{2}\b/.test(keptAll)) add(id, 'flow', 'PERSONAL DATA STORED', '');
    /* the record: every class passed (by today's number), transfer credit marked as such, this term's classes to My Classes */
    const cn = await page.evaluate(cs => Object.fromEntries(cs.map(c => [c, (window.TCPL && TCPL.canon(c)) || c])), [...new Set(K.done.concat(K.taking, K.transfer, hist.map(h => h.code)))]);
    const hc = new Set(hist.map(h => cn[h.code] || h.code));
    const lost = K.done.filter(c => !hc.has(cn[c] || c));
    if (lost.length) add(id, 'flow', 'a passed class missing from Past classes', lost.slice(0, 8));
    const xf = new Set(K.transfer.map(c => cn[c] || c));
    const xbad = hist.filter(h => xf.has(cn[h.code] || h.code) !== /^🌍/.test(h.professor || ''));
    if (K.icons && xbad.length) add(id, 'flow', 'transfer credit marked wrong on the record', xbad.slice(0, 6).map(h => h.code + (h.professor ? ' (marked)' : ' (not marked)')));
    const mine = posted('saved_classes').map(r => cn[r.code] || r.code);
    const tk = K.taking.map(c => cn[c] || c).filter(c => !mine.includes(c));
    if (tk.length) add(id, 'flow', 'a class being taken missing from My Classes', tk);
    /* failed-only classes: never a finished class on the record */
    const histCodes = new Set(hist.map(h => h.code));
    const fo = (K.failed_only || []).filter(c => histCodes.has(c));
    if (fo.length) add(id, 'flow', 'failed / withdrawn class saved as taken', fo);
    /* Past classes: the count, what's left, and no semester flowchart on a quarter catalog */
    const st = await page.evaluate(() => {
      plSync(); const g = plGate(); const L = g.L, X = auditLines(TC.audit, L);
      const R = L ? planRank(L) : null;
      const left = X ? X.open.filter(b => !auditIsTotal(b)).length : null;
      const done = new Set(); const taking = [...takingCodes()];
      return { F: X ? X.filled.length : null, N: X ? X.live.length : null, left, picks: R ? R.all.map(c => c.code) : [], ledgerDone: L ? (L.doneCodes || []) : [], taking, completed: TCPL.completed().map(c => TCPL.canon(c) || c),
               fhd: false, err: null };
    });
    if (st.F !== K.past.filled || st.N !== K.past.total || st.left !== K.past.left) add(id, 'flow', 'Past classes counts', `${st.F} of ${st.N} filled, ${st.left} left — key ${K.past.filled} of ${K.past.total}, ${K.past.left} left`);
    (globalThis.__stats = globalThis.__stats || []).push({ id, picks: st.picks.length, left: st.left });
    const fdone = (K.failed_only || []).filter(c => st.completed.includes(c));
    if (fdone.length) add(id, 'flow', 'a class never passed counts as completed (prerequisites, the Builder)', fdone);
    const bad = st.picks.filter(c => K.done.includes(c) || K.taking.includes(c));
    if (bad.length) add(id, 'flow', 'Builder picks a class already done or being taken', bad);
    await page.evaluate(() => { S.tab = 'schedule'; S.schedTab = 'past'; save(); render(true); }); await page.waitForTimeout(1200);
    const flowYears = await page.locator('.pc-fhd, [data-a="plYear"]').count();
    if (/Quarter/.test(K.catalog) && flowYears) add(id, 'flow', 'semester flowchart shown on a quarter catalog', flowYears);
    /* reload: read back the same */
    await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 12000 }); await page.waitForTimeout(1500);
    await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 10000 }); await page.waitForTimeout(300);
    const st2 = await page.evaluate(() => { plSync(); const g = plGate(); const X = auditLines(TC.audit, g.L); return { F: X ? X.filled.length : null, N: X ? X.live.length : null }; });
    if (st2.F !== st.F || st2.N !== st.N) add(id, 'flow', 'reload reads back differently', `${JSON.stringify(st2)} vs ${JSON.stringify({ F: st.F, N: st.N })}`);
    if (log.errors.length) add(id, 'flow', 'page errors', log.errors.slice(0, 3));
  } catch (e) { add(id, 'flow', 'threw', String(e.message || e).slice(0, 300)); }
  finally { await close(); }
}
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25', MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '2274', label: 'Spring 2027' }] };
/* the shipped config's shape for the Fall of year y: picking the Spring after (Cal Poly's codes: 2 + yy + 8 Fall / 4 Spring) */
function termsFor(y) {
  if (y === 2026) return SPRING_CFG;
  const f = '2' + String(y).slice(2) + '8', sp = '2' + String(y + 1).slice(2) + '4';
  return { TERM: sp, TERM_LABEL: 'Spring ' + (y + 1), NOW_TERM: f, NOW_LABEL: 'Fall ' + y, NOW_UNTIL: (y + 1) + '-01-25', MY_TERMS: [{ code: f, label: 'Fall ' + y }, { code: sp, label: 'Spring ' + (y + 1) }] };
}
function synthTables(major, standing, K, CFG = SPRING_CFG) {
  const T = globalThis.__synthTables(major, standing);
  const codes = new Set();
  Object.values(K.lines).forEach(k => k.options.forEach(c => codes.add(c)));
  K.done.concat(K.taking, K.failed_only || []).forEach(c => codes.add(c));
  const base = T.course_seats[0]; let n = 81000;
  [...codes].filter(c => /^[A-Z]{2,5} \d{4}[A-Z]?$/.test(c)).forEach((c, i) => {
    for (const term of [CFG.TERM, CFG.NOW_TERM]) T.course_seats.push(Object.assign({}, base, { term, course_code: c, title: c, section: '01', class_nbr: String(n++), days: ['MoWe', 'TuTh', 'MoWeFr'][i % 3] + ' ' + ['9:10AM - 10:00AM', '11:10AM - 12:00PM', '2:10PM - 3:00PM'][i % 3], status: 'Open', available: 10, enrolled: 30, waitlist_total: 0, instructor: 'Fixture, Prof' }));
  });
  return T;
}

/* ---------------------------------------------------------------- run */
const t0 = Date.now();
await readerPass();
console.log(`reader: ${ids.length} reports in ${Math.round((Date.now() - t0) / 1000)}s`);
if (FLOW) {
  const FX = await import('./app-fixtures.mjs');
  const { NOREC } = await import('./base-fixtures.mjs').catch(() => ({}));
  globalThis.__synthTables = (major, standing) => {
    const T = JSON.parse(JSON.stringify(FX.TABLES));
    const me = FX.ME.id;
    for (const t of ['class_history', 'my_sections', 'saved_classes', 'degree_audit', 'plans', 'flowchart_marks', 'class_waivers', 'commitments']) if (Array.isArray(T[t])) T[t] = T[t].filter(r => r.user_id !== me);
    T.planner_prefs = T.planner_prefs || [];
    T.profiles = T.profiles.map(p => p.id === me ? Object.assign({}, p, { major, class_standing: standing, concentration: null }) : p);
    return T;
  };
  let next = 0; const t1 = Date.now();
  await Promise.all(Array.from({ length: workers }, async (_, w) => { while (next < ids.length) { const id = ids[next++]; await flowOne(id, 8300 + w); } }));
  console.log(`flow: ${ids.length} reports in ${Math.round((Date.now() - t1) / 1000)}s`);
}
/* the summary: findings by kind, and which scenarios they come from */
const byWhat = {};
for (const [id, fs_] of Object.entries(results)) for (const f of fs_) (byWhat[f.layer + ': ' + f.what] = byWhat[f.layer + ': ' + f.what] || []).push(id);
const clean = ids.filter(id => !results[id]);
console.log(`\n${clean.length} of ${ids.length} reports with no finding`);
for (const [w, list] of Object.entries(byWhat).sort((a, b) => b[1].length - a[1].length)) console.log(`  ${String(new Set(list).size).padStart(3)} reports · ${w}   e.g. ${[...new Set(list)].slice(0, 4).join(', ')}`);
if (globalThis.__stats) { const z = globalThis.__stats; console.log(`Builder: ${z.filter(x => x.picks).length} of ${z.length} reports got picks (${z.reduce((a, x) => a + x.picks, 0)} in all)`); }
const out = opt('--json', '');
if (out) fs.writeFileSync(out, JSON.stringify({ ids, results }, null, 1));
process.exit(clean.length === ids.length ? 0 : 1);
