#!/usr/bin/env python3
"""Past classes as option A, and the Builder opens with what's left (Tate, 2026-10-11).

Tate picked option A of the canvas *Past Classes by Catalog* ("What's left first"), then: "past classes should display at
the very top the classes you have left that should be where Builder takes over and be at the top of builder, (2 left to
graduate) then show the best feasable options that fulfil those classes."

- Past classes: the card opens with your major (and concentration) and your catalog, then "N left to graduate" (the
  report's open lines, or "left on your flowchart" without one), each listed, and one button into the Builder. Then a
  Done card (Major and support · Concentration · GE · Degree, each opening to its lines with a report), then "Every
  class, by term": your record by the terms you took it in — Year 1 from your first Cal Poly term, quarters tagged,
  semesters tagged, transfer and AP credit apart — each class with what your report counted it for.
- Builder: the same "N left to graduate" on top, and under each requirement the best feasible sections for the term
  (no clash with the plan or your work, by your priorities), each with + Plan A. Replaces "More picks".
Usage: python3 past-left-builder-top-2026-10-11.py <repo-dir>   (replayable on build 19:58)"""
import sys, os, re
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)

# ---------------------------------------------------------------- CSS
rep(".pc-k.full .pc-kv{color:var(--teal-t,var(--teal))}", """.pc-k.full .pc-kv{color:var(--teal-t,var(--teal))}
/* Past classes, option A (2026-10-11): what's left first */
.pc-mec{flex-wrap:nowrap;align-items:flex-start;gap:10px}
.pc-mw{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px}
.pc-catc{flex:none;font-size:12px;font-weight:900;padding:4px 10px;border-radius:99px;white-space:nowrap}
.pc-catc.q{background:var(--amber-soft);color:var(--amber-ink)}
.pc-catc.s{background:var(--blue-soft);color:var(--blue-ink)}
.pc-left{display:flex;align-items:baseline;gap:10px;margin-top:4px}
.pc-left b{font-size:42px;font-weight:1000;line-height:1}
.pc-left span{font-size:18px;font-weight:900}
.pc-nrow{display:flex;align-items:baseline;flex-wrap:wrap;gap:6px;margin-top:8px}
.pc-nrow .pc-num{margin:0}
.pc-inp{font-size:14px;font-weight:800;color:var(--amber-ink)}
.pc-sum .pc-num b{font-size:15px}
.pc-sum .pc-num span{font-size:14px}
.pc-lrows{margin-top:14px;display:flex;flex-direction:column;gap:6px}
.pc-lrows .pc-row{background:var(--bg)}
.pc-lrow{display:flex;align-items:flex-start;gap:12px;width:100%;background:var(--bg);border-radius:14px;padding:10px 12px;min-height:52px;text-align:left}
.pc-lring{width:20px;height:20px;flex:none;border-radius:50%;box-shadow:inset 0 0 0 2.5px var(--ink5,var(--muted));margin-top:2px}
.pc-ltx{flex:1;min-width:0;display:flex;flex-direction:column;gap:6px}
.pc-ltx b{font-size:15px;font-weight:900;line-height:1.25}
.pc-lchips{display:flex;flex-wrap:wrap;gap:6px}
.pc-lchips .code{font-size:12px;padding:3px 8px}
.pc-lmore{display:block;min-height:40px;font-size:14px;font-weight:900;color:var(--blue-t,var(--blue));text-align:left}
.pc-sum .pc-go{border-top:0;margin-top:10px;padding:0 16px;min-height:50px;border-radius:16px;background:var(--blue);color:#fff;justify-content:center}
.pc-sum .pc-go span{flex:none}
.pc-sum .pc-go em{color:rgba(255,255,255,.8)}
.pc-done{margin-top:12px;padding:8px 16px 6px}
.pc-dh{font-size:12.5px;font-weight:900;letter-spacing:.08em;color:var(--muted);padding:6px 0 4px}
.pc-done .pc-year > span:first-child{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.pc-done .pc-year{background:none;border-radius:0;padding:0;margin-top:0;border-top:1px solid var(--line);min-height:54px}
.pc-done .pc-year:first-of-type,.pc-done .pc-dh + .pc-year{border-top:0}
.pc-done .pc-open .pc-year{margin-bottom:0}
.pc-done .pc-term{margin:0 -8px 8px}
.pc-year .pc-dbar{flex:none;width:48px;height:6px;border-radius:3px;background:var(--track,var(--fill2));overflow:hidden}
.pc-dbar i{display:block;height:100%;background:var(--teal-t,var(--teal))}
.pc-done .pc-kinds{margin-top:4px;padding-top:0;border-top:0}
.pc-terms{display:flex;align-items:center;gap:12px;width:calc(100% - 0px);margin-top:12px;min-height:62px;padding:0 16px;border-radius:20px;background:var(--tint1);text-align:left}
.pc-terms .pc-tt{flex:1;min-width:0}
.pc-terms b{display:block;font-size:16px;font-weight:900}
.pc-terms span span{display:block;font-size:13px;font-weight:800;color:var(--muted)}
/* every class, by term */
.pc-tv{padding:6px 12px 0}
.pc-tvh{display:flex;align-items:center;gap:10px;padding:8px 0 4px}
.pc-tvh h2{flex:1;margin:0;font-size:21px;font-weight:900}
.pc-ty{margin-top:10px;padding:4px 14px 8px}
.pc-tyh{display:flex;align-items:center;gap:10px;width:100%;min-height:56px;text-align:left}
.pc-tyh .pc-tt{flex:1;min-width:0}
.pc-tyh b{display:block;font-size:17px;font-weight:900}
.pc-tyh span span{display:block;font-size:13px;font-weight:800;margin-top:1px}
.pc-tyh .q{color:var(--amber-ink)}.pc-tyh .s{color:var(--blue-ink)}.pc-tyh .x{color:var(--purple-ink)}
.pc-th{display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:900;letter-spacing:.08em;color:var(--muted);padding:12px 0 2px}
.pc-tag{font-size:11px;font-weight:900;letter-spacing:0;padding:2px 8px;border-radius:99px}
.pc-tag.q{background:var(--amber-soft);color:var(--amber-ink)}.pc-tag.s{background:var(--blue-soft);color:var(--blue-ink)}
.pc-trow{display:flex;flex-direction:column;gap:5px;width:100%;padding:10px 0;border-top:1px solid var(--line);text-align:left}
.pc-th + .pc-trow{border-top:0}
.pc-trow .pc-t1{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap}
.pc-trow .pc-cc{font-size:15px;font-weight:900}
.pc-was,.pc-tn{font-size:13px;font-weight:800;color:var(--muted)}
.pc-cf{display:flex;flex-wrap:wrap;gap:5px}
.pc-cf i{font-style:normal;font-size:12px;font-weight:900;padding:3px 9px;border-radius:99px;white-space:nowrap}
.pc-cf .g{background:var(--teal-soft);color:var(--teal-t,var(--teal))}
.pc-cf .m{background:var(--blue-soft);color:var(--blue-ink)}
.pc-cf .c{background:var(--amber-soft);color:var(--amber-ink)}
.pc-cf .d{background:var(--purple-soft);color:var(--purple-ink)}
.pc-cf .u{background:var(--fill);color:var(--ink3)}
/* the Builder, opening on what's left (2026-10-11) */
.pll{margin:12px 12px 0;padding:16px 14px 8px}
.pll-h{display:flex;align-items:baseline;gap:10px;padding:0 2px}
.pll-h b{font-size:40px;font-weight:1000;line-height:1}
.pll-h span{font-size:18px;font-weight:900}
.pll-s{font-size:13.5px;font-weight:800;color:var(--muted);padding:4px 2px 0;line-height:1.4}
.pll-req{border-top:1px solid var(--line);padding:12px 0 6px;margin-top:12px}
.pll-req:first-of-type{margin-top:12px}
.pll-rh{display:flex;align-items:flex-start;gap:10px;padding:0 2px 6px}
.pll-ring{width:20px;height:20px;flex:none;border-radius:50%;box-shadow:inset 0 0 0 2.5px var(--ink5,var(--muted));margin-top:1px}
.pll-rl{font-size:16px;font-weight:900;line-height:1.3}
.pll-opt{display:flex;align-items:center;gap:10px;background:var(--bg);border-radius:16px;padding:10px 10px 10px 12px;margin:6px 0 0 30px}
.pll-opt.clash{opacity:.75}
.pll-main{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px;text-align:left}
.pll-top{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.pll-top .code{font-size:12.5px;padding:3px 8px}
.pll-nm{font-size:14.5px;font-weight:900;line-height:1.25}
.pll-meta{font-size:12.5px;font-weight:800;color:var(--ink4);line-height:1.35}
.pll-warn{font-size:12.5px;font-weight:800;color:var(--red-ink)}
.pll-add{flex:none;height:38px;padding:0 12px;border-radius:99px;background:var(--blue);color:#fff;font-size:13.5px;font-weight:900;white-space:nowrap;display:inline-flex;align-items:center;gap:4px}
.pll-add.on{background:var(--card);color:var(--blue-t,var(--blue));box-shadow:inset 0 0 0 2px var(--blue)}
.pll-more{display:block;margin:4px 0 0 30px;min-height:36px;font-size:13.5px;font-weight:900;color:var(--blue-t,var(--blue))}
.pll-none{margin:2px 0 0 30px;font-size:13.5px;font-weight:800;color:var(--muted);line-height:1.4}
.pll-none button{color:var(--blue-t,var(--blue));font-weight:900;min-height:32px}
.pll-all{display:block;width:100%;min-height:46px;border-top:1px solid var(--line);margin-top:10px;font-size:14.5px;font-weight:900;color:var(--blue-t,var(--blue));text-align:left;padding:0 2px}""", 'css')

# ---------------------------------------------------------------- Past classes: the summary card
i = S.index('function pcSummary(L, P) {'); j = S.index('\n}\n', i) + 3
S = S[:i] + r"""function pcSummary(L, P) {
  const X = auditLines(TC.audit, L);
  /* (2026-10-11) with a report in, its count: filled of every line it prints (the Planner's count) — and the
     report's catalog, so a quarter-catalog student can see the app checks THAT, not the semester flowchart */
  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L || { major: (P || TC.profile || {}).major }, { F, N }); }
  const cat = X && TC.audit.catalog ? `<div class="pc-cat">Your catalog: ${esc(TC.audit.catalog)}${TC.audit.printed_on ? ' · report printed ' + esc(pcDate(TC.audit.printed_on)) : ''}</div>` : '';
  const pct = L.N ? Math.round(100 * L.F / L.N) : 0;
  const conc = TCPL.concInfo(L.major);
  /* (2026-10-11) never ask for a concentration your report already names (the report decides) */
  const pick = L.concUnchosen && conc.list.length && !(X && TC.audit.conc) ? `<div class="pc-conc"><div class="b" style="font-size:14.5px;margin-bottom:8px">Pick your concentration</div><div style="display:flex;flex-wrap:wrap;gap:8px">${conc.list.map(c => `<button class="chip" style="background:var(--bg)" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  /* (2026-10-11, option A) what's left first, then one way into the Builder, which takes it from there */
  const lf = pcLeft(L, X);
  const go = lf.n ? `<button class="pc-link pc-go" data-a="pcReport"><span>Best options in the Builder</span>${pcChev()}</button>` : '';
  return `<div class="card pc-sum">${pcWho(L, P)}${lf.head}<div class="pc-nrow"><div class="pc-num"><b>${L.F} of ${L.N}</b><span>filled</span></div>${lf.inp ? `<span class="pc-inp">· ${lf.inp} in progress</span>` : ''}</div><div class="pc-bar" role="img" aria-label="${L.F} of ${L.N} filled"><i style="width:${pct}%"></i></div>${lf.rows}${go}${cat}${pick}</div>${pcDone(L, X)}${pcTermsBtn()}`;
}
/* (2026-10-11) What's left: the report's open lines (and the ones it couldn't read), or the flowchart's spots to do. */
function pcLeft(L, X) {
  UI.pcLeftAll = !!UI.pcLeftAll;
  if (X) {
    /* the count is requirements, like the Builder's; the total-units line is listed ("N units to go") but not counted */
    const idx = new Map((TC.audit.reqs || []).map((b, i) => [b, i])), items = X.open.concat(X.unknown), n = X.open.filter(b => !auditIsTotal(b)).length;
    const inp = X.inprog.length;
    const head = n ? `<div class="pc-left"><b>${n}</b><span>left to graduate</span></div>` : `<div class="pc-left pc-alldone"><span>${X.open.length ? 'Only units left on your report' : 'Nothing left on your report'}</span></div>`;
    const show = UI.pcLeftAll ? items : items.slice(0, 6);
    /* the lines you're finishing this term: one tap away, not in the way (2026-10-11) */
    const ip = X.inprog.filter(b => !X.open.includes(b) && !X.unknown.includes(b)), ipOpen = !!UI.pcInpOpen;
    const ipRows = ip.length ? `<button class="pc-lmore pc-inpb" data-a="pcInpOpen" aria-expanded="${ipOpen}">${ipOpen ? 'Hide' : 'Show'} the ${ip.length} in progress this term</button>${ipOpen ? ip.map(b => pcReqRow(b, X, L, idx.get(b))).join('') : ''}` : '';
    const rows = items.length || ip.length ? `<div class="pc-lrows">${show.map(b => pcReqRow(b, X, L, idx.get(b))).join('')}${items.length > show.length ? `<button class="pc-lmore" data-a="pcLeftAll">All ${items.length} ›</button>` : ''}${ipRows}</div>` : '';
    return { n, head, rows, inp };
  }
  if (!L || !L.need) return { n: 0, head: '', rows: '' };
  const items = L.need.map(n => ({ n, ge: false })).concat(L.needU.map(n => ({ n, ge: n.type === 'ge' })));
  const n = items.length;
  const head = n ? `<div class="pc-left"><b>${n}</b><span>left on your flowchart</span></div>` : `<div class="pc-left pc-alldone"><span>Nothing left on your flowchart</span></div>`;
  const row = ({ n: q, ge }) => {
    if (ge || !q.codes) return `<button class="pc-lrow" ${q.type === 'ge' ? `data-a="plGe" data-x="${esc(q.area || '')}"` : 'data-a="pcReport"'}><span class="pc-lring" aria-hidden="true"></span><span class="pc-ltx"><b>${esc(q.title)}</b><span class="pc-lchips"><span class="code" style="background:var(--purple-soft);color:var(--purple-ink)">${q.type === 'ge' ? 'GE' : 'Elective'}</span></span></span></button>`;
    const code = q.codes.find(c => COURSES[c]) || q.codes[0];
    const nm = q.choice ? q.title : (q.title && !codeLike(q.title) ? q.title : courseName(code) || code);
    const chips = q.codes.slice(0, 3).map(c => `<span class="code">${esc(c)}</span>`).join('') + (q.codes.length > 3 ? `<span class="code">+${q.codes.length - 3}</span>` : '');
    return `<button class="pc-lrow" data-a="${COURSES[code] ? 'openClass' : 'pcReport'}" data-x="${esc(code)}"><span class="pc-lring" aria-hidden="true"></span><span class="pc-ltx"><b>${esc(nm)}</b><span class="pc-lchips">${chips}</span></span></button>`;
  };
  const show = UI.pcLeftAll ? items : items.slice(0, 4);
  const rows = n ? `<div class="pc-lrows">${show.map(row).join('')}${n > show.length ? `<button class="pc-lmore" data-a="pcLeftAll">All ${n} ›</button>` : ''}</div>` : '';
  return { n, head, rows, inp: L.T || 0 };
}
/* (2026-10-11) Done: with a report, its groups (each opens to its filled lines); without, the flowchart's kinds. */
function pcDone(L, X) {
  if (!X) { const k = pcKinds(L, null); return k ? `<div class="card pc-done"><div class="pc-dh">DONE</div>${k}</div>` : ''; }
  UI.pcGroups = UI.pcGroups || {};
  const idx = new Map((TC.audit.reqs || []).map((b, i) => [b, i])), left = new Set(X.open.concat(X.unknown));
  const rows = PC_GROUPS.map(([key, label]) => {
    const all = X.live.filter(b => pcGroupOf(b) === key); if (!all.length) return '';
    const done = all.filter(b => !left.has(b)), f = done.length, open = !!UI.pcGroups[key];
    const lab = key === 'conc' && TC.audit.conc ? esc(TC.audit.conc) : label, pct = Math.round(100 * f / all.length);
    const head = `<button class="pc-year" data-a="pcGroup" data-x="${key}" aria-expanded="${open}" aria-label="${lab}, ${f} of ${all.length} filled"><span>${lab}</span><span class="pc-dbar" aria-hidden="true"><i style="width:${pct}%"></i></span><em>${f} of ${all.length}</em>${pcChev(open ? 90 : 0)}</button>`;
    return open && done.length ? `<div class="pc-open">${head}<div class="pc-term pc-grp">${done.map(b => pcReqRow(b, X, L, idx.get(b))).join('')}</div></div>` : head;
  }).join('');
  return rows ? `<div class="card pc-done"><div class="pc-dh">DONE</div>${rows}</div>` : '';
}
/* (2026-10-11) Every class, by term: the way in */
function pcTermsBtn() {
  const n = pcHist().length + [...nowCodes()].filter(c => !(TC.myHistory || []).some(h => pcK(h.code) === pcK(c))).length;
  if (!n) return '';
  const q = (TC.myHistory || []).some(h => !pcXfer(h) && pcQtr(h.term, h.year));
  return `<button class="pc-terms" data-a="pcTerms">${ic('cal', 22, 2.2)}<span class="pc-tt"><b>Every class, by term</b><span>${n} class${n === 1 ? '' : 'es'}${q ? ' · quarters, then semesters' : ''}</span></span>${pcChev()}</button>`;
}
/* Cal Poly's first semester was Fall 2026: every term before it was a quarter. */
const pcQtr = (t, y) => +y < 2026 || (+y === 2026 && t !== 'Fall');
/* (2026-10-11) Every class, by term. Year 1 is the academic year (Fall to Summer) of your first Cal Poly term;
   transfer and AP credit sit apart (the report posts it in a term you didn't take it in). Each class says what
   your report counted it for, or "Units only". */
function pcTermsView() {
  UI.pcTermYr = UI.pcTermYr || {};
  const X = TC.audit ? auditLines(TC.audit, null) : null;
  const ORD = { Fall: 0, Winter: 1, Spring: 2, Summer: 3 };
  const ay = h => h.term === 'Fall' ? +h.year : +h.year - 1;
  const hist = pcHist(), xfer = hist.filter(pcXfer), real = hist.filter(h => !pcXfer(h) && h.term && +h.year);
  const nowT = String(nowTerm().label || '').split(' '), have = new Set((TC.myHistory || []).map(h => pcK(h.code)));
  const now = [...nowCodes()].map(pcK).filter((c, i, a) => a.indexOf(c) === i && !have.has(c)).map(c => ({ code: c, term: nowT[0], year: +nowT[1], now: true }));
  const rows = real.concat(now.filter(r => ORD[r.term] != null && r.year));
  const undated = hist.filter(h => !pcXfer(h) && !(h.term && +h.year));
  /* what each class counted for, from the report: matched by number (today's or as printed) and term */
  const forOf = h => {
    if (!X) return null;
    const k = pcK(h.code), t = h.term && h.year ? h.term + ' ' + h.year : '';
    const out = []; let was = '';
    X.live.forEach(b => (b.used || []).forEach(e => { if ((pcK(e.n || e.c) === k || pcK(e.c) === k) && (!e.t || !t || e.t === t)) { if (!out.includes(b)) out.push(b); if (String(e.c || '').replace(/\s+/g, ' ').trim().toUpperCase() !== k && !was) was = e.c; } }));
    return { lines: out, was };
  };
  const chip = b => {
    const g = pcGroupOf(b), lab = String(b.label || '');
    if (g === 'ge') { const m = /^(?:Area\s+)?([A-F][1-4]?(?:\s?UD)?|[1-6][A-C]?|UD\s?[0-9/]+)\s*(?:\(Qtr\))?\s*:/.exec(lab); return `<i class="g">GE${m ? ' ' + esc(m[1]) : ''}</i>`; }
    if (g === 'conc') return `<i class="c">${esc(TC.audit && TC.audit.conc ? TC.audit.conc : 'Concentration')}</i>`;
    if (g === 'degree') return `<i class="d">${b.kind === 'uscp' ? 'USCP' : b.kind === 'gwr' ? 'Writing requirement' : esc(lab.slice(0, 28))}</i>`;
    return `<i class="m">${b.kind === 'elective' ? 'Elective' : 'Major'}${/^[A-Z]{2,5}[ /]/.test(lab) ? '' : ' · ' + esc(lab.replace(/\s*(course|requirement)s?$/i, '').slice(0, 30))}</i>`;
  };
  const row = h => {
    const code = pcK(h.code), nm = courseName(code), f = forOf(h);
    const ip = h.now || histNotDone(h);
    const cf = (f && f.lines.length ? f.lines.map(chip).join('') : '') + (ip ? '<i class="c">In progress</i>' : f && !f.lines.length ? '<i class="u">Units only</i>' : '');
    const act = h.now ? (COURSES[code] ? `data-a="openClass" data-x="${esc(code)}" data-y="now"` : '') : `data-a="pcOpen" data-x="${esc(pcKey(h))}"`;
    return `<button class="pc-trow" ${act}><span class="pc-t1"><span class="pc-cc">${esc(code)}</span>${f && f.was ? `<span class="pc-was">was ${esc(f.was)}</span>` : ''}${nm ? `<span class="pc-tn">· ${esc(nm)}</span>` : ''}</span>${cf ? `<span class="pc-cf">${cf}</span>` : ''}</button>`;
  };
  const first = rows.length ? Math.min(...rows.map(ay)) : 0;
  const years = {}; rows.forEach(h => { const y = ay(h); (years[y] = years[y] || []).push(h); });
  const ys = Object.keys(years).map(Number).sort((a, b) => b - a), latest = ys[0];
  const yCard = y => {
    const list = years[y], q = list.every(h => pcQtr(h.term, h.year)), s = list.every(h => !pcQtr(h.term, h.year));
    const open = UI.pcTermYr[y] !== undefined ? UI.pcTermYr[y] : y === latest;
    const kind = q ? '<span class="q">Quarters</span>' : s ? '<span class="s">Semesters</span>' : '<span class="q">Quarters, then semesters</span>';
    const nowTag = list.some(h => h.now) ? ' · now' : '';
    const head = `<button class="pc-tyh" data-a="pcTermYr" data-x="${y}" aria-expanded="${open}"><span class="pc-tt"><b>Year ${y - first + 1} · ${y}–${String(y + 1).slice(2)}${nowTag}</b><span>${kind.replace('</span>', ` · ${list.length} class${list.length === 1 ? '' : 'es'}</span>`)}</span></span>${pcChev(open ? 90 : 0)}</button>`;
    if (!open) return `<div class="card pc-ty">${head}</div>`;
    const terms = {}; list.forEach(h => { const k = h.term + ' ' + h.year; (terms[k] = terms[k] || []).push(h); });
    const tk = Object.keys(terms).sort((a, b) => { const [ta, ya] = a.split(' '), [tb, yb] = b.split(' '); return (+ya - +yb) || ((ORD[ta] ?? 9) - (ORD[tb] ?? 9)); });
    return `<div class="card pc-ty">${head}${tk.map(k => { const [t, yy] = k.split(' '); return `<div class="pc-th">${esc(k.toUpperCase())} <span class="pc-tag ${pcQtr(t, yy) ? 'q' : 's'}">${pcQtr(t, yy) ? 'quarter' : 'semester'}</span></div>${terms[k].map(row).join('')}`; }).join('')}</div>`;
  };
  const xOpen = !!UI.pcTermYr.x;
  const xCard = xfer.length ? `<div class="card pc-ty"><button class="pc-tyh" data-a="pcTermYr" data-x="x" aria-expanded="${xOpen}"><span class="pc-tt"><b>Transfer and AP credit</b><span><span class="x">${xfer.length} · not tied to a term you took</span></span></span>${pcChev(xOpen ? 90 : 0)}</button>${xOpen ? xfer.map(row).join('') : ''}</div>` : '';
  const uCard = undated.length ? `<div class="card pc-ty"><div class="pc-th">NO TERM ON RECORD</div>${undated.map(row).join('')}</div>` : '';
  const cat = X && TC.audit.catalog ? `<span class="pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}">${/quarter/i.test(TC.audit.catalog) ? 'Quarter catalog' : 'Semester catalog'}</span>` : '';
  return `<div class="pc-tv"><div class="pc-tvh"><button class="iconbtn" data-a="pcTerms" aria-label="Back to Past classes">${ic('chevL', 20, 2.6)}</button><h2>Every class, by term</h2></div>${ys.map(yCard).join('')}${xCard}${uCard}</div>`;
}
""" + S[j:]

# pcWho: the catalog chip
rep("""  const conc = c0 ? `<span>${esc(c0)} concentration</span>` : '';
  return `<div class="pc-me"><b>${esc(major)}</b>${conc}</div>`;""",
    """  const conc = c0 ? `<span>${esc(c0)} concentration</span>` : '';
  /* (2026-10-11) the catalog your report judges you by */
  const cat = TC.audit && TC.audit.catalog ? (/quarter/i.test(TC.audit.catalog) ? '<span class="pc-catc q">Quarter catalog</span>' : '<span class="pc-catc s">Semester catalog</span>') : '';
  return cat ? `<div class="pc-me pc-mec"><div class="pc-mw"><b>${esc(major)}</b>${conc}</div>${cat}</div>` : `<div class="pc-me"><b>${esc(major)}</b>${conc}</div>`;""", 'pcWho chip')

# pcReportView: the still card and the groups moved up (left, Done)
rep("""  const still = X.open.concat(X.unknown, X.inprog.filter(b => !X.open.includes(b)));
  const stillCard = still.length ? `<div class="card pc-still"><div class="pc-hd"><span>Still needed</span><em>${X.open.length + X.unknown.length}</em></div>${still.map(b => pcReqRow(b, X, L, idx.get(b))).join('')}</div>`
    : `<div class="card pc-still pc-alldone"><div class="pc-hd"><span>Nothing left on your report</span></div></div>`;
  const groups = PC_GROUPS.map(([key, label]) => {""", """  /* (2026-10-11, option A) what's left is on top (pcLeft) and the groups are the Done card (pcDone) */
  const still = X.open.concat(X.unknown);
  const stillCard = '';
  const groups = [].map(([key, label]) => {""", 'report view')

# pastView: the by-term page
rep("""  const { L, P } = g, none = plNoRecord();
  pcPlace(L);""", """  const { L, P } = g, none = plNoRecord();
  pcPlace(L);
  if (UI.pcTerms) return pcTermsView();""", 'pastView terms')

# actions
rep("""  pcGroup: key => { UI.pcGroups = UI.pcGroups || {}; UI.pcGroups[key] = !UI.pcGroups[key]; render(true); },""",
    """  pcGroup: key => { UI.pcGroups = UI.pcGroups || {}; UI.pcGroups[key] = !UI.pcGroups[key]; render(true); },
  pcLeftAll: () => { UI.pcLeftAll = !UI.pcLeftAll; render(true); },
  pcInpOpen: () => { UI.pcInpOpen = !UI.pcInpOpen; render(true); },
  pcTerms: () => { UI.pcTerms = !UI.pcTerms; render(); },
  pcTermYr: y => { UI.pcTermYr = UI.pcTermYr || {}; const latest = UI.pcTermYr[y] === undefined && document.querySelector(`[data-a="pcTermYr"][data-x="${y}"][aria-expanded="true"]`); UI.pcTermYr[y] = latest ? false : !UI.pcTermYr[y]; render(true); },
  plLeftAll: () => { UI.plLeftAll = !UI.plLeftAll; render(true); },
  plLeftOpen: k => { UI.plLeftOpen = UI.plLeftOpen || {}; UI.plLeftOpen[k] = !UI.plLeftOpen[k]; render(true); },""", 'actions')

# leaving Schedule's Past classes closes the by-term page
rep("""  schedTab: t => { if (t !== 'planner') UI.plFor = null; S.schedTab = t; save(); render(); },""",
    """  schedTab: t => { if (t !== 'planner') UI.plFor = null; UI.pcTerms = false; S.schedTab = t; save(); render(); },""", 'schedTab')

# ---------------------------------------------------------------- the Builder: what's left, then the best options
rep("""/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */""", r"""/* (2026-10-11) Tate: "the classes you have left … should be where Builder takes over and be at the top of builder
   (2 left to graduate) then show the best feasable options that fulfil those classes." Each requirement left — the
   report's open lines, or the flowchart's — with the best options for it, in the Builder's own order (your priorities:
   degree, professors, friends), each in the section that fits the plan open below (no clash with its classes or your
   work); one that can't fit says so. */
function plLeftReqs(R, L) {
  if (R.audit && R.X) return R.X.open.filter(b => !auditIsTotal(b)).map(b => ({ key: 'a' + TC.audit.reqs.indexOf(b), label: b.label || 'Requirement', opts: (b.options || []).length, cands: R.all.filter(c => (c.fills || []).includes(b)), area: plGeArea(b).length === 1 ? plGeArea(b)[0] : '' }));
  return L.need.map((n, i) => ({ key: 'n' + i, label: n.choice ? n.title : (n.title && !codeLike(n.title) ? n.title : courseName(n.codes[0]) || n.codes[0]), opts: n.codes.length, one: n.codes.length === 1 ? n.codes[0] : '', cands: R.all.filter(c => c.n === n), area: '' }))
    .concat(L.needU.map((n, i) => ({ key: 'u' + i, label: n.title, cands: n.type === 'ge' && n.area ? R.all.filter(c => c.geA.includes(n.area)) : [], area: n.type === 'ge' ? n.area || '' : '' })));
}
function plLeftSec(c, k) {
  if (c.inPlan === k && c.planSec) return c.planSec;
  return plDraftSec(c.code, planSecsOf(k).filter(s => s.code !== c.code), null);
}
function plLeftOpt(c, k, label) {
  const fit = plLeftSec(c, k), sec = fit || c.planSec || c.best, r = pickReason(c);
  const rt = sec && sec.prof ? ratingOf(sec.prof) : null, fr = sec ? friendsInSec(sec.id) : [];
  const when = !sec ? '' : sec.async ? 'Online · anytime' : sec.s == null ? 'Time not posted' : `${daysLabel(sec.days)} ${hs(sec.s)}–${hs(sec.e)}`;
  const prof = sec && sec.prof ? profName(sec.prof).split(' ').slice(-1)[0] + (rt != null ? ` ★ ${rt.toFixed(1)}` : '') : 'Instructor not listed';
  const meta = [when, prof, fr.length ? `${fr.length} friend${fr.length === 1 ? '' : 's'}` : '', regOpen() && sec ? String(secSeatText(sec)).replace(/<[^>]*>/g, '') : ''].filter(Boolean).join(' · ');   /* the seat words, not their markup (found on real Spring 2027 sections) */
  const tag = r.t === 'Counts twice' || /^Unlocks/.test(r.t) || r.t === 'Catch up' ? `<span class="pk-tag ${r.k}">${esc(r.t)}</span>` : '';
  const btn = !sec ? '' : c.inPlan ? `<button class="pll-add on" data-a="addPlanSheet" data-x="${esc(sec.id)}" aria-label="${esc(c.code)} is in Plan ${c.inPlan} — change">${ic('check', 15, 3)} Plan ${c.inPlan}</button>` : `<button class="pll-add" data-a="addPlanSheet" data-x="${esc(sec.id)}" aria-label="Add ${esc(c.code)} to Plan ${k}">+ Plan ${k}</button>`;
  return `<div class="pll-opt${fit || c.inPlan ? '' : ' clash'}"><button class="pll-main" data-a="pickWhy" data-x="${esc(c.code)}"><span class="pll-top"><span class="code">${esc(c.code)}</span>${tag}</span>${(() => { const nm = courseName(c.code) || course(c.code).title || ''; return nm && nm.toLowerCase() !== String(label || '').toLowerCase() ? `<span class="pll-nm">${esc(nm)}</span>` : ''; })()}<span class="pll-meta">${esc(meta)}</span>${fit || c.inPlan ? '' : `<span class="pll-warn">Every section clashes with Plan ${k} or your week</span>`}</button>${btn}</div>`;
}
function plLeftCard(R, L, k) {
  const reqs = plLeftReqs(R, L); if (!reqs.length) return '';
  const pos = c => R.all.indexOf(c), fits = c => !!(c.inPlan || plLeftSec(c, k));
  /* feasible first, then the Builder's order; requirements with a feasible option first */
  reqs.forEach(q => q.cands.sort((a, b) => (fits(b) ? 1 : 0) - (fits(a) ? 1 : 0) || pos(a) - pos(b)));
  const rk = q => q.cands.length ? (fits(q.cands[0]) ? 0 : 1e6) + pos(q.cands[0]) : 2e6;
  reqs.sort((a, b) => rk(a) - rk(b));
  UI.plLeftOpen = UI.plLeftOpen || {};
  const show = UI.plLeftAll ? reqs : reqs.slice(0, 4);
  const X = R.X, tot = X && X.total && X.total.status === 'not' && X.total.units && X.total.units.need != null ? auditNum(X.total.units.need) : null;
  const row = q => {
    const all = !!UI.plLeftOpen[q.key], cs = q.cands.slice(0, all ? 6 : 2);
    const none = q.cands.length ? '' : `<div class="pll-none">${q.area ? `Nothing for GE ${esc(q.area)} fits yet. <button data-a="plGe" data-x="${esc(q.area)}">See GE ${esc(q.area)} classes</button>`
      : q.opts === 0 ? 'Your report doesn’t name the classes for this one. Your advisor or the catalog has the list.'
      : `${q.one ? `${esc(q.one)} isn’t` : q.opts === 1 ? 'Its class isn’t' : 'None of its classes are'} offered in ${esc(CFG.TERM_LABEL)}${UI.pl && UI.pl.prereqs ? ', or you need a prerequisite first' : ''}.`}</div>`;
    const more = q.cands.length > 2 ? `<button class="pll-more" data-a="plLeftOpen" data-x="${q.key}">${all ? 'Fewer' : `${Math.min(q.cands.length, 6) - 2} more option${Math.min(q.cands.length, 6) - 2 === 1 ? '' : 's'}`}</button>` : '';
    return `<div class="pll-req"><div class="pll-rh"><span class="pll-ring" aria-hidden="true"></span><span class="pll-rl">${esc(q.label)}</span></div>${cs.map(c => plLeftOpt(c, k, q.label)).join('')}${none}${more}</div>`;
  };
  const sub = `Best options for ${esc(CFG.TERM_LABEL)}${tot ? ` · plus ${tot} units to go` : ''}`;
  return `<div class="card pll"><div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div><div class="pll-s">${sub}</div>${show.map(row).join('')}${reqs.length > 4 ? `<button class="pll-all" data-a="plLeftAll">${UI.plLeftAll ? 'Fewer' : `All ${reqs.length} ›`}</button>` : ''}</div>`;
}
/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */""", 'builder left card')

rep("""  return `<div class="pl-top"><div>${term}<div class="pl-sub">${R.left} requirement${R.left === 1 ? '' : 's'} left</div></div>""",
    """  return `<div class="pl-top"><div>${term}</div>""", 'builder top line')
rep("""  ${asked ? '' : cmAskCard()}
  ${waiting ? cmWaitCard(k) : planCard(k, L, R, data ? '' : 'nodata')}
  <div class="pl-sech"><span>More picks</span>${more.length > 3 ? `<button class="pl-more" data-a="plMoreAll">${UI.plMoreAll ? 'Fewer' : `All ${more.length}`} ›</button>` : ''}</div>
  ${shown.length ? `<div class="pl-picks">${shown.map(pickCard).join('')}</div>` : `<div class="pk-empty">Nothing else on the ${esc(CFG.TERM_LABEL)} list fits what you still need${UI.pl.prereqs ? ' — or you need a prerequisite first' : ''}.</div>`}""",
    """  ${asked ? '' : cmAskCard()}
  ${plLeftCard(R, L, k)}
  ${waiting ? cmWaitCard(k) : planCard(k, L, R, data ? '' : 'nodata')}""", 'builder body')

rep("Nothing fits yet — add classes from the picks below.", "Nothing fits yet — add one of the options above.", 'plan empty')
rep("`Nothing fits Plan ${k} yet — add classes from the picks below`", "`Nothing fits Plan ${k} yet — add one of the options above`", 'draft toast')
open(PA, 'w', encoding='utf-8').write(S); print('past-left-builder-top: done')
