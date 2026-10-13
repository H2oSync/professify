/* Prototype (2026-10-11, not in the app): report lines → 2026–28 flowchart spots by course number, then requirement name, then GE area; the rest stay their own rows.
   Run from app-dev/tests: node ../proto/catalog-match-2026-10-11.mjs <report.pdf …> [-v]. Reports stay outside the repo. */
import { openApp } from '/home/claude/app2/gitwork/app-dev/tests/app-harness.mjs';
import fs from 'node:fs'; import path from 'node:path';
const files = process.argv.slice(2).filter(f => f.endsWith('.pdf')), verbose = process.argv.includes('-v');
const { page, close } = await openApp({ port: 8282 });
await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
const all = {};
for (const f of files) {
  const r = await page.evaluate(async b64 => {
    const MAJ = { BUS: 'Business Administration', ENVM: 'Environmental Management & Protection', ITP: 'Industrial Technology & Packaging', PSY: 'Psychology', REC: 'Experience & Event Management' };
    const lib = await loadPdfJs(); const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const doc = await lib.getDocument({ data: bytes, isOffscreenCanvasSupported: false }).promise; const text = await dprDocText(doc);
    const p = TCPL.dprParse(text), a = p.audit || {}, R = p.rows || [], prog = p.program || {};
    const K = c => (TCPL.canon(c) || String(c || '').toUpperCase().trim());
    /* a cross-listed number ("NR/LA 2218") is each of its listings */
    const KX = c => { const m = /^([A-Z]{2,5}(?:\/[A-Z]{2,5})+)\s+(\d{3,4}[A-Z]?)$/.exec(String(c || '').toUpperCase().trim()); return m ? m[1].split('/').map(x => K(x + ' ' + m[2])) : [K(c)]; };
    const quarter = /quarter/i.test(a.catalog || ''), major = MAJ[prog.major] || prog.major;
    const idx = {}, names = {}; Object.keys(COURSES).forEach(c => { idx[c] = 1; names[c] = COURSES[c].title; });
    TCPL.set({ student: { major, conc: prog.conc || '', standing: '' }, history: R.filter(x => !x._now).map(x => ({ code: x.cur, term: x.term, year: x.year })), classes: R.filter(x => x._now).map(x => x.cur), waived: {}, index: idx, names, marks: [] });
    const L = TCPL.ledger();
    if (!L) return { err: 'no flowchart for ' + major };
    const spots = []; L.grid.forEach((t, ti) => t.slots.forEach(s => spots.push(Object.assign({ fy: t.year, ft: t.term, ti }, s, { codesK: [...new Set([...(s.choice || []), ...(s.codes || []), s.code].filter(Boolean).flatMap(KX))] }))));
    const est = { done: spots.filter(s => s.state === 'done').length, taking: spots.filter(s => s.state === 'taking').length, need: spots.filter(s => s.state === 'need').length, cant: spots.filter(s => s.state === 'cant').length };
    /* the report's lines → units to place */
    const DEG = /^(units|gpa|gwr|uscp)$/;
    const live = (a.reqs || []).filter(b => b && !b.flag);
    const isDeg = b => DEG.test(b.kind || '') || /^GE:\s*(Total|Residence|Upper Division) Units/i.test(b.label || '');
    const deg = live.filter(isDeg);
    const units = [];
    /* a degree-wide line that names a course ("PSY 3372 (USCP)") is a spot like any other; the rest sit under Degree requirements */
    const coded = b => (b.options || []).some(c => /^[A-Z]{2,5} \d{3,4}/.test(c));
    live.filter(b => !isDeg(b) || coded(b)).forEach((b, li) => {
      const need = b.courses && b.courses.need != null ? +b.courses.need : 1, used = b.used || [];
      /* a "pick N" line fills N spots, one class each; any other line is one spot, with every class it used (a lecture and its lab) */
      if (need > 1) { const n = Math.max(need, used.length); for (let i = 0; i < n; i++) units.push({ li, b, u: used[i] || null, us: used[i] ? [used[i]] : [], i, n }); }
      else units.push({ li, b, u: used[0] || null, us: used, i: 0, n: 1 });
    });
    const norm = s => String(s || '').toLowerCase().replace(/&/g, ' and ').replace(/\(.*?\)/g, ' ').replace(/\b(course|courses|elective|electives|concentration|requirement|select|one|the|a|an|of|in)\b/g, ' ').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
    const taken = new Set(), how = { course: 0, name: 0, ge: 0, geAny: 0 };
    const place = (unit, s, rule) => { taken.add(s); unit.spot = s; unit.rule = rule; how[rule]++; };
    /* rule 1: course numbers */
    units.forEach(un => { if (un.spot || un.b.kind === 'ge') return;
      const opts = new Set([...(un.b.options || []), ...(un.b.label.match(/\b[A-Z]{2,5}(?:\/[A-Z]{2,5})* \d{4}[A-Z]?\b/g) || []), ...(un.u ? [un.u.n || un.u.c] : [])].flatMap(KX));
      const s = spots.find(s => !taken.has(s) && s.type !== 'ge' && s.codesK.some(c => opts.has(c))); if (s) place(un, s, 'course'); });
    /* rule 2: same requirement name */
    units.forEach(un => { if (un.spot) return; const ln = norm(un.b.label); if (!ln || ln.length < 6) return;
      const s = spots.find(s => !taken.has(s) && s.type !== 'ge' && !/^free elective/i.test(s.title) && !s.codesK.length && norm(s.title) && (norm(s.title) === ln || (norm(s.title).length >= 8 && ln.includes(norm(s.title))) || (ln.length >= 8 && norm(s.title).includes(ln)))); if (s) place(un, s, 'name'); });
    /* rule 3: GE area by the registrar's table */
    units.forEach(un => { if (un.spot || un.b.kind !== 'ge') return; const ar = plGeArea(un.b); if (ar.length !== 1) return;
      const s = spots.find(s => !taken.has(s) && s.type === 'ge' && s.area === ar[0]); if (s) place(un, s, 'ge'); });
    /* rule 3b: a GE line the report filled, on a flowchart whose GE spots name no area ("GE Requirement", "GE Elective") */
    units.forEach(un => { if (un.spot || un.b.kind !== 'ge' || un.b.status === 'not') return;
      const s = spots.find(s => !taken.has(s) && s.type === 'ge' && !s.area); if (s) place(un, s, 'geAny'); });
    how.geAny = how.geAny || 0;
    const st = b => b.status === 'satisfied' ? ((b.used || []).some(e => e.p) ? 'taking' : 'done') : b.status === 'in_progress' ? 'taking' : b.status === 'not' ? 'need' : 'cant';
    const own = units.filter(u => !u.spot), freeEl = spots.filter(s => !taken.has(s) && /^free elective/i.test(s.title)), freeSpots = spots.filter(s => !taken.has(s) && !freeEl.includes(s));
    /* classes the report counted for no line: the free-elective pool */
    const usedKeys = new Set(live.flatMap(b => (b.used || []).map(e => K(e.n || e.c))));
    const pool = R.filter(x => !usedKeys.has(K(x.cur)) && !usedKeys.has(K(x.code)));
    /* invariants */
    const inv = [];
    const lineSeen = new Set(units.map(u => u.li)); if (lineSeen.size !== live.filter(b => !isDeg(b) || coded(b)).length) inv.push('a line is missing');
    const usedAll = live.flatMap(b => (b.used || []).map(e => K(e.n || e.c) + '|' + (e.t || '')));
    const usedShown = units.flatMap(u => u.us).concat(deg.filter(b => !coded(b)).flatMap(b => b.used || [])).map(e => K(e.n || e.c) + '|' + (e.t || ''));
    const notShown = usedAll.filter(x => !usedShown.includes(x)); if (notShown.length) inv.push('used classes not shown: ' + notShown.length + ' ' + notShown.join(',') + ' in ' + live.filter(b => (b.used || []).some(e => notShown.includes(K(e.n || e.c) + '|' + (e.t || '')))).map(b => b.label.slice(0, 40) + ' need=' + JSON.stringify(b.courses) + ' used=' + (b.used || []).length).join(' / '));
    const dbl = usedShown.filter((x, i, a) => a.indexOf(x) !== i); 
    /* timeline from the record */
    const ORD = { Winter: 1, Spring: 2, Summer: 3, Fall: 4 };
    const real = R.filter(x => !x._xfer), xfer = R.filter(x => x._xfer);
    const ay = x => (x.term === 'Fall' ? +x.year : +x.year - 1);  // academic year starts in Fall
    const firstAY = real.length ? Math.min(...real.map(ay)) : null;
    const isQ = x => +x.year < 2026 || (+x.year === 2026 && x.term !== 'Fall');
    const years = {}; real.forEach(x => { const y = ay(x) - firstAY + 1; (years[y] = years[y] || new Set()).add(x.term + ' ' + x.year + (isQ(x) ? ' (q)' : '')); });
    const yearNow = real.length ? ay({ term: 'Fall', year: 2026 }) - firstAY + 1 : null;
    const kind = quarter ? 'stayed on quarter catalog' : real.some(isQ) ? 'quarter start, switched to semester catalog' : 'semester only';
    return { major, conc: prog.conc, catalog: a.catalog, kind, yearNow, years: Object.fromEntries(Object.entries(years).map(([k, v]) => [k, [...v]])), xfer: xfer.length,
      est, lines: live.length, deg: deg.length, units: units.length, how, own: own.length, ownSat: own.filter(u => st(u.b) !== 'need').length,
      freeSpots: freeSpots.length, freeEl: freeEl.length, pool: pool.map(x => x.code + ' ' + x.term + ' ' + x.year + (x._xfer ? ' xfer' : '') + (x._now ? ' now' : '')), freeByState: freeSpots.reduce((m, s) => (m[s.state] = (m[s.state] || 0) + 1, m), {}),
      agree: units.filter(u => u.spot).filter(u => (st(u.b) === 'need') === (u.spot.state === 'need')).length, matched: units.filter(u => u.spot).length,
      upgrade: units.filter(u => u.spot && st(u.b) !== 'need' && (u.spot.state === 'need' || u.spot.state === 'cant')).map(u => `${u.spot.title} ← ${u.u ? u.u.c + (u.u.n ? '→' + u.u.n : '') + ' ' + (u.u.t || '') : u.b.label} [${u.rule}]`),
      downgrade: units.filter(u => u.spot && st(u.b) === 'need' && u.spot.state === 'done').map(u => `${u.spot.title}: report open, flowchart said done`),
      ownList: own.map(u => `${u.b.kind}|${u.b.label.slice(0, 60)}|${st(u.b)}|${u.u ? u.u.c + ' ' + (u.u.t || '') + (u.u.x ? ' xfer' : '') : ''}`),
      freeList: freeSpots.map(s => `Y${s.fy} ${s.ft}: ${s.title} [${s.codesK.join('/') || s.type}${s.area ? ' ' + s.area : ''}] ${s.state}`),
      matchList: units.filter(u => u.spot).map(u => `${u.rule}: ${u.spot.title} ← ${u.b.label.slice(0, 50)} ${u.u ? '(' + u.u.c + ' ' + (u.u.t || '') + ')' : ''} ${st(u.b)}`),
      inv, dbl: dbl.length };
  }, fs.readFileSync(f).toString('base64'));
  const n = path.basename(f); all[n] = r;
  if (r.err) { console.log(n, r.err); continue; }
  console.log(`\n### ${n} — ${r.major}${r.conc ? ' · ' + r.conc : ''} · ${r.catalog} · ${r.kind} · year ${r.yearNow} · transfer ${r.xfer}`);
  console.log(`   flowchart-only estimate: ${JSON.stringify(r.est)}`);
  console.log(`   report: ${r.lines} lines (${r.deg} degree-wide) → ${r.units} units; matched ${r.matched} (${JSON.stringify(r.how)}); own rows ${r.own} (${r.ownSat} met); spots left ${r.freeSpots} ${JSON.stringify(r.freeByState)} + ${r.freeEl} free-elective spots ← pool of ${r.pool.length} unused classes; status agree ${r.agree}/${r.matched}; invariants ${r.inv.length ? r.inv.join('; ') : 'OK'}; double-used ${r.dbl}`);
  console.log(`   years: ${JSON.stringify(r.years)}`);
  console.log(`   report fixes the flowchart (${r.upgrade.length}): ${r.upgrade.join(' · ')}`);
  if (r.downgrade.length) console.log(`   report reopens: ${r.downgrade.join(' · ')}`);
  if (verbose) { console.log('   OWN:\n     ' + r.ownList.join('\n     ')); console.log('   FREE SPOTS:\n     ' + r.freeList.join('\n     ')); console.log('   MATCHES:\n     ' + r.matchList.join('\n     ')); }
}
fs.writeFileSync('/tmp/claude-0/oc/match-out.json', JSON.stringify(all));
await close();
