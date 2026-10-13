#!/usr/bin/env python3
"""Past classes, option A; Every class, by term, option B (Tate, 2026-10-12, on the Past Classes Rework canvas: "I like
A. but make B how "every class, by term" looks just take out this" — B's header: the Past classes title, its + and the
Major / Fin. Mgmt / GE / Degree chips).

A · Past classes with a report:
  - one answer first: a ring and "N left to graduate", "F of N filled · <catalog> catalog", "See them in the Builder ›"
    (the whole card opens the Builder, where what's left lives);
  - DONE SO FAR: a group still short keeps its bar and "f of n"; a finished one shows only "✓ All n" (✓ Both, ✓ Done);
  - Every class, by term and Units only as two slim rows of one card (Units only still unfolds in place);
  - + Log a class and Upload a new report as two quiet links at the bottom.
B · Every class, by term: a timeline, newest first. A dot per term (the term being taken: a blue dot, its card open, "In
  progress"); each term folds to one line ("quarter · 4 classes"); "SWITCHED TO SEMESTERS" once between the last quarter
  and the first semester; past 6 terms the oldest fold into one dashed row ("Fall 2023 – Spring 2024 · 3 quarters"). A
  class reads "CODE  what it counted for" ("was BUS 310 · Major", "GE A2", "In progress"); one the report counted for
  nothing reads "Extra · counted for nothing"; credit earned at another school since your first term wears a globe.
  Credit from before Cal Poly and classes with no term keep their own cards at the end.
Replayable on 18:05 (+ the 2026-10-12 report patches).  python3 past-classes-a-2026-10-12.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'past-classes-a: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)

# ---- CSS ----
rep(""".pc-trow .pc-cc{font-size:15px;font-weight:900}
""", """.pc-trow .pc-cc{font-size:15px;font-weight:900}
/* (2026-10-12) Past classes A: the answer first, then what's done, then two slim rows; quiet actions */
.pc-hero{display:flex;align-items:center;gap:16px;width:100%;margin-top:12px;padding:16px;background:var(--card);border-radius:20px;text-align:left;color:var(--ink)}
.pc-hero svg{flex:none}
.pc-hero .pc-ra{stroke:var(--track,var(--fill2))}.pc-hero .pc-rb{stroke:var(--teal-t,var(--teal))}.pc-hero text{fill:var(--ink);font-family:inherit;font-weight:900}
.pc-htx{display:flex;flex-direction:column;gap:3px;min-width:0}
.pc-htx b{font-size:21px;font-weight:900;letter-spacing:-.01em}
.pc-htx span{font-size:13.5px;font-weight:700;color:var(--ink4)}
.pc-htx em{font-style:normal;font-size:13px;font-weight:900;color:var(--blue-t,var(--blue))}
.pc-dok{font-style:normal;font-size:14px;font-weight:900;color:var(--teal-t,var(--teal));white-space:nowrap}
.pc-links{margin-top:12px;padding:0 16px}
.pc-lk{display:flex;align-items:center;gap:12px;width:100%;min-height:62px;text-align:left;border-top:1px solid var(--line)}
.pc-links > .pc-lk:first-child{border-top:0}
.pc-lk > svg:first-child{flex:none;color:var(--blue-t,var(--blue))}
.pc-lk.pc-uh > svg:first-child{color:var(--ink4)}
.pc-lk .pc-tt{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.pc-lk b{font-size:15.5px;font-weight:900}
.pc-lk .pc-tt span{font-size:12.5px;font-weight:800;color:var(--muted)}
.pc-links .pc-orow:last-child{padding-bottom:8px}
.pc-btns.pc-qb{justify-content:center;gap:22px;margin:10px 0 4px}
.pc-qb .pc-btn{flex:none;background:none;color:var(--blue-t,var(--blue));min-height:44px;padding:0 6px}
/* (2026-10-12) Every class, by term: a timeline */
.pc-tl{display:flex;gap:12px}
.pc-tlr{display:flex;flex-direction:column;align-items:center;width:16px;flex:none}
.pc-tld{width:10px;height:10px;border-radius:50%;background:var(--teal-t,var(--teal));margin-top:21px;flex:none}
.pc-tld.now{width:14px;height:14px;background:var(--blue);box-shadow:0 0 0 3px var(--blue-soft);margin-top:19px}
.pc-tlr i{flex:1;width:2px;background:var(--track,var(--fill2));margin-top:4px}
.pc-tlc{flex:1;min-width:0;background:var(--card);border-radius:18px;margin-bottom:8px;padding:0 14px}
.pc-tlh{display:flex;align-items:center;gap:8px;width:100%;min-height:52px;text-align:left;color:var(--ink)}
.pc-tlh b{font-size:16px;font-weight:900;white-space:nowrap}
.pc-tlnow{font-size:12px;font-weight:900;color:var(--blue-ink);background:var(--blue-soft);padding:3px 8px;border-radius:99px;white-space:nowrap}
.pc-tlm{margin-left:auto;font-size:12.5px;font-weight:800;color:var(--muted);white-space:nowrap}
.pc-tlb{padding:0 0 6px}
.pc-tlb .pc-trow{flex-direction:row;align-items:center;gap:10px;padding:10px 0;min-height:44px}
.pc-tlb .pc-trow:first-child{border-top:1px solid var(--line)}
.pc-tlb .pc-cc{flex:none;min-width:82px;font-size:14.5px;font-weight:900;color:var(--ink);background:none;padding:0;border-radius:0}
.pc-tw{min-width:0;font-size:13px;font-weight:700;color:var(--ink4)}
.pc-tw.u{color:var(--amber-ink);font-weight:800}
.pc-tw.p{color:var(--blue-ink);font-weight:800}
.pc-glb{flex:none;color:var(--blue-t,var(--blue));margin-right:-4px}
.pc-tsw{display:flex;align-items:center;gap:12px;padding:2px 0 10px 28px;font-size:11.5px;font-weight:900;letter-spacing:.12em;color:var(--ink4)}
.pc-tsw::after{content:'';flex:1;height:1px;background:var(--track,var(--fill2))}
.pc-tlold{display:flex;align-items:center;gap:8px;width:100%;min-height:50px;padding:0 14px;border:1px dashed var(--line2);border-radius:16px;margin-bottom:8px;text-align:left;font-size:14.5px;font-weight:900;color:var(--ink4)}
.pc-tlold span{flex:1}
""")

rep(""".pc-trow .pc-t1{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap}
""", "")
rep(""".pc-tyh .q{color:var(--amber-ink)}.pc-tyh .s{color:var(--blue-ink)}.pc-tyh .x{color:var(--purple-ink)}""", """.pc-tyh .x{color:var(--purple-ink)}""")
rep(""".pc-was,.pc-tn{font-size:13px;font-weight:800;color:var(--muted)}
.pc-cf{display:flex;flex-wrap:wrap;gap:5px}
.pc-cf i{font-style:normal;font-size:12px;font-weight:900;padding:3px 9px;border-radius:99px;white-space:nowrap}
.pc-cf .g{background:var(--teal-soft);color:var(--teal-t,var(--teal))}
.pc-cf .m{background:var(--blue-soft);color:var(--blue-ink)}
.pc-cf .c{background:var(--amber-soft);color:var(--amber-ink)}
.pc-cf .d{background:var(--purple-soft);color:var(--purple-ink)}
.pc-cf .u{background:var(--fill);color:var(--ink3)}
""", "")   # the year cards' chips: the timeline's rows read as words

# ---- A: the answer first; Done; two slim rows; quiet actions ----
rep("""function pcSummary(L, P) {
  const X = auditLines(TC.audit, L);
  return `${pcDone(L, X)}${pcTermsBtn()}`;
}""", """function pcSummary(L, P, fresh) {
  const X = auditLines(TC.audit, L);
  /* (2026-10-12, Tate's option A) with a report: one answer first, then what's done; the way into Every class, by term
     sits with Units only (pcReportView) */
  if (X && fresh) return `${pcHero(X)}${pcDone(L, X)}`;
  return `${pcDone(L, X)}${pcTermsBtn()}`;
}
/* (2026-10-12) the answer first: how close you are, and what's left — which lives in the Builder, one tap away */
function pcHero(X) {
  const n = X.open.filter(b => !auditIsTotal(b)).length, u = X.unknown.length, F = X.filled.length, N = X.live.length;
  if (!N) return '';
  const pct = Math.min(n || u ? 99 : 100, Math.round(100 * F / N));
  const C = 2 * Math.PI * 35, arc = Math.max(0, Math.min(C, C * F / Math.max(1, N)));
  const ring = `<svg width="84" height="84" viewBox="0 0 84 84" aria-hidden="true"><circle class="pc-ra" cx="42" cy="42" r="35" fill="none" stroke-width="9"/><circle class="pc-rb" cx="42" cy="42" r="35" fill="none" stroke-width="9" stroke-linecap="round" stroke-dasharray="${arc.toFixed(1)} ${C.toFixed(1)}" transform="rotate(-90 42 42)"/><text x="42" y="48" text-anchor="middle" font-size="19">${pct}%</text></svg>`;
  /* lines the app couldn't read are never "nothing left": the Builder lists them */
  const head = n ? `${n} left to graduate` : u ? `${u} line${u === 1 ? '' : 's'} we couldn’t read` : X.open.length ? 'Only units left' : 'Nothing left on your report';
  const sub = `${F} of ${N} filled${TC.audit && TC.audit.catalog ? ' · ' + esc(TC.audit.catalog) + ' catalog' : ''}`;
  const k = n || u;
  return k ? `<button class="pc-hero" data-a="schedTab" data-x="planner" aria-label="${esc(head)}, ${F} of ${N} filled. See them in the Builder">${ring}<span class="pc-htx"><b>${esc(head)}</b><span>${sub}</span><em>See ${k === 1 ? 'it' : 'them'} in the Builder ›</em></span></button>`
    : `<div class="pc-hero">${ring}<span class="pc-htx"><b>${esc(head)}</b><span>${sub}</span></span></div>`;
}""")
rep("""  if (X) return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L, P) + pcReportView(X, L) + pcBtns()}</div>`;""",
    """  if (X) return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L, P, true) + pcReportView(X, L) + pcBtns()}</div>`;""")
rep("""    const lab = key === 'conc' && TC.audit.conc ? esc(TC.audit.conc) : label, pct = Math.round(100 * f / all.length);
    const head = `<button class="pc-year" data-a="pcGroup" data-x="${key}" aria-expanded="${open}" aria-label="${lab}, ${f} of ${all.length} filled"><span>${lab}</span><span class="pc-dbar" aria-hidden="true"><i style="width:${pct}%"></i></span><em>${f} of ${all.length}</em>${pcChev(open ? 90 : 0)}</button>`;""",
    """    const lab = key === 'conc' && TC.audit.conc ? esc(TC.audit.conc) : label, pct = Math.round(100 * f / all.length);
    /* (2026-10-12) a finished group goes quiet: a check, no bar */
    const n = all.length, fin = f === n, ok = n === 1 ? '✓ Done' : n === 2 ? '✓ Both' : `✓ All ${n}`;
    const head = `<button class="pc-year" data-a="pcGroup" data-x="${key}" aria-expanded="${open}" aria-label="${lab}, ${f} of ${n} filled"><span>${lab}</span>${fin ? `<em class="pc-dok">${ok}</em>` : `<span class="pc-dbar" aria-hidden="true"><i style="width:${pct}%"></i></span><em>${f} of ${n}</em>`}${pcChev(open ? 90 : 0)}</button>`;""")
rep("""  return rows ? `<div class="card pc-done"><div class="pc-dh">DONE</div>${rows}</div>` : '';
}
/* (2026-10-11) Every class, by term: the way in */""", """  return rows ? `<div class="card pc-done"><div class="pc-dh">DONE SO FAR</div>${rows}</div>` : '';
}
/* (2026-10-11) Every class, by term: the way in */""")
rep("""function pcTermsBtn() {
  const n = pcHist().length + [...nowCodes()].filter(c => !(TC.myHistory || []).some(h => pcK(h.code) === pcK(c))).length;
  if (!n) return '';
  const q = (TC.myHistory || []).some(h => !pcXfer(h) && pcQtr(h.term, h.year));
  return `<button class="pc-terms" data-a="pcTerms">${ic('cal', 22, 2.2)}<span class="pc-tt"><b>Every class, by term</b><span>${n} class${n === 1 ? '' : 'es'}${q ? ' · quarters, then semesters' : ''}</span></span>${pcChev()}</button>`;
}""", """function pcTermsBtn(slim) {
  const n = pcHist().length + [...nowCodes()].filter(c => !(TC.myHistory || []).some(h => pcK(h.code) === pcK(c))).length;
  if (!n) return '';
  const q = (TC.myHistory || []).some(h => !pcXfer(h) && pcQtr(h.term, h.year));
  return `<button class="${slim ? 'pc-lk' : 'pc-terms'}" data-a="pcTerms">${ic('cal', slim ? 20 : 22, 2.2)}<span class="pc-tt"><b>Every class, by term</b><span>${n} class${n === 1 ? '' : 'es'}${q ? ' · quarters, then semesters' : ''}</span></span>${pcChev()}</button>`;
}""")
rep("""  const unitsOnly = rest.length ? `<div class="card pc-oth pc-uo"><button class="pc-uh" data-a="pcUnits" aria-expanded="${uOpen}"><span class="pc-tt"><b>Units only</b><span>${rest.length} on your record, counted for no requirement</span></span>${pcChev(uOpen ? 90 : 0)}</button>${uOpen ? rest.map(h => { const code = pcK(h.code); return `<div class="pc-orow"><div class="pc-tx"><button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}"><span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(courseName(code))}</span></button>${pcXfer(h) && !courseName(code) ? xLine(h) : pcLine(code, histNotDone(h) ? 'taking' : 'done', h)}${histNotDone(h) ? pcNowTag : ''}</div></div>`; }).join('') : ''}</div>` : '';""",
    """  /* (2026-10-12, option A) Every class, by term and Units only: two slim rows of one card */
  const minus = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M8.5 12h7"/></svg>';
  const uRows = uOpen ? rest.map(h => { const code = pcK(h.code); return `<div class="pc-orow"><div class="pc-tx"><button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}"><span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(courseName(code))}</span></button>${pcXfer(h) && !courseName(code) ? xLine(h) : pcLine(code, histNotDone(h) ? 'taking' : 'done', h)}${histNotDone(h) ? pcNowTag : ''}</div></div>`; }).join('') : '';
  const uBtn = rest.length ? `<button class="pc-lk pc-uh" data-a="pcUnits" aria-expanded="${uOpen}">${minus}<span class="pc-tt"><b>Units only</b><span>${rest.length} class${rest.length === 1 ? '' : 'es'} that counted for no requirement</span></span>${pcChev(uOpen ? 90 : 0)}</button>${uRows}` : '';
  const tBtn = pcTermsBtn(true);
  const unitsOnly = tBtn || uBtn ? `<div class="card pc-links${uBtn ? ' pc-uo' : ''}">${tBtn}${uBtn}</div>` : '';""")
rep("""const pcBtns = () => `<div class="pc-btns"><button class="pc-btn" data-a="sheet" data-x="logClass">+ Log a class</button><label class="pc-btn">Upload report<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label></div>`;""",
    """/* (2026-10-12, option A) rare actions: two quiet links */
const pcBtns = () => `<div class="pc-btns pc-qb"><button class="pc-btn" data-a="sheet" data-x="logClass">+ Log a class</button><label class="pc-btn">${TC.audit ? 'Upload a new report' : 'Upload report'}<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label></div>`;""")

# ---- B: Every class, by term as a timeline ----
rep("""    if (!X) return null;
    const k = pcK(h.code), t = h.term && h.year ? h.term + ' ' + h.year : '';""", """    if (!X || !X.live.some(b => Array.isArray(b.used))) return null;   /* an older report kept no classes per line (2026-10-12) */
    const k = pcK(h.code), t = h.term && h.year ? h.term + ' ' + h.year : '';""")
rep("""  const ay = h => h.term === 'Fall' ? +h.year : +h.year - 1;\n""", "")   # years aren't the unit any more
i = s.index("  const first = rows.length ? Math.min(...rows.map(ay)) : 0;\n  const years = {};")
j = s.index("  return `<div class=\"pc-tv\"><div class=\"pc-tvh\">", i)
j2 = s.index("\n}\n", j)
OLD_TAIL = s[i:j2]
NEW_TAIL = r"""  /* (2026-10-12, Tate's option B) a timeline, newest first: a dot per term, each term folds to one line; the term being
     taken is open; "SWITCHED TO SEMESTERS" once; past 6 terms the oldest fold into one row */
  UI.pcTermOpen = UI.pcTermOpen || {};
  const globe = '<svg class="pc-glb" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-label="Other school" role="img"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg>';
  const word = b => {
    const g = pcGroupOf(b), lab = String(b.label || '');
    if (g === 'ge') { const m = /^(?:Area\s+)?([A-F][1-4]?(?:\s?UD)?|[1-6][A-C]?|UD\s?[0-9/]+)\s*(?:\(Qtr\))?\s*:/.exec(lab); return 'GE' + (m ? ' ' + m[1] : ''); }
    if (g === 'conc') return TC.audit && TC.audit.conc ? TC.audit.conc : 'Concentration';
    if (g === 'degree') return b.kind === 'uscp' ? 'USCP' : b.kind === 'gwr' ? 'Writing requirement' : lab.slice(0, 28);
    /* a label the report shouts ("TECHNOLOGY MANAGEMENT COURSE:") reads as words */
    let t = lab.split(':')[0].trim(); if ((t.match(/[a-z]/g) || []).length < (t.match(/[A-Z]/g) || []).length / 4) t = t.toLowerCase().replace(/\b[a-z]/g, c => c.toUpperCase());
    return (b.kind === 'elective' ? 'Elective' : 'Major') + (/^[A-Z]{2,5}[ /]/.test(lab) ? '' : ' · ' + t.replace(/\s*(course|requirement)s?$/i, '').slice(0, 30));
  };
  const nowK = nowT.join(' ');
  const trow = h => {
    const code = pcK(h.code), f = forOf(h), ip = h.now || histNotDone(h);
    const parts = [];
    if (f && f.was) parts.push('was ' + f.was);
    /* (a class from another school wears the globe, which says so) */
    if (f && f.lines.length) f.lines.forEach(b => { const w = word(b); if (!parts.includes(w)) parts.push(w); });
    /* in the term being taken, its pill already says so */
    const here = (h.term + ' ' + h.year) === nowK, cls = ip ? (here ? '' : ' p') : f && !f.lines.length ? ' u' : '';
    if (ip) { if (!here) parts.push('In progress'); } else if (f && !f.lines.length) parts.push('Extra · counted for nothing');
    const act = h.now ? (COURSES[code] ? `data-a="openClass" data-x="${esc(code)}" data-y="now"` : '') : `data-a="pcOpen" data-x="${esc(pcKey(h))}"`;
    const inner = `${h.oth ? globe : ''}<span class="pc-cc">${esc(code)}</span><span class="pc-tw${cls}">${esc(parts.join(' · ') || courseName(code) || '')}</span>`;
    return act ? `<button class="pc-trow" ${act}>${inner}</button>` : `<div class="pc-trow">${inner}</div>`;
  };
  const terms = {}; rows.forEach(h => { const k = h.term + ' ' + h.year; (terms[k] = terms[k] || []).push(h); });
  const CAL = { Winter: 1, Spring: 2, Summer: 3, Fall: 4 }, ck = k => { const [t, y] = k.split(' '); return (+y) * 10 + (CAL[t] || 0); };
  const keys = Object.keys(terms).sort((a, b) => ck(b) - ck(a));
  const newest = keys[0];
  const qOf = k => { const [t, y] = k.split(' '); return pcQtr(t, y); };
  const tCard = (k, last) => {
    const list = terms[k], isNow = list.some(h => h.now || histNotDone(h)) && k === nowK;
    const open = UI.pcTermOpen[k] !== undefined ? UI.pcTermOpen[k] : k === newest;
    /* the term being taken wears its pill instead of the quarter / semester word (the divider says which) */
    const meta = `${isNow ? '' : (qOf(k) ? 'quarter · ' : 'semester · ')}${list.length} class${list.length === 1 ? '' : 'es'}${list.some(h => h.oth) ? ' · other school' : ''}`;
    const head = `<button class="pc-tlh" data-a="pcTermOpen" data-x="${esc(k)}" aria-expanded="${open}"><b>${esc(k)}</b>${isNow ? '<span class="pc-tlnow">In progress</span>' : ''}<span class="pc-tlm">${meta}</span>${pcChev(open ? 90 : 0)}</button>`;
    return `<div class="pc-tl"><div class="pc-tlr"><span class="pc-tld${isNow ? ' now' : ''}"></span>${last ? '' : '<i></i>'}</div><div class="pc-tlc">${head}${open ? `<div class="pc-tlb">${list.map(trow).join('')}</div>` : ''}</div></div>`;
  };
  const SHOW = 6, oldOpen = !!UI.pcTermOld, shown = keys.length > SHOW && !oldOpen ? keys.slice(0, SHOW - 1) : keys, hidden = keys.slice(shown.length);
  let html = '';
  shown.forEach((k, i) => {
    html += tCard(k, i === shown.length - 1 && !hidden.length);
    const nx = shown[i + 1] || hidden[0];
    if (nx && !qOf(k) && qOf(nx)) html += '<div class="pc-tsw" role="separator">SWITCHED TO SEMESTERS</div>';
  });
  if (hidden.length) {
    const allQ = hidden.every(qOf), allS = hidden.every(k => !qOf(k));
    html += `<button class="pc-tlold" data-a="pcTermOld" aria-expanded="false" aria-label="Show ${hidden.length} older terms"><span>${esc(hidden[hidden.length - 1])} – ${esc(hidden[0])} · ${hidden.length} ${allQ ? 'quarters' : allS ? 'semesters' : 'terms'}</span>${pcChev()}</button>`;
  }
  const xOpen = !!UI.pcTermYr.x;
  const xCard = xfer.length ? `<div class="card pc-ty"><button class="pc-tyh" data-a="pcTermYr" data-x="x" aria-expanded="${xOpen}"><span class="pc-tt"><b>Credit from other schools</b><span><span class="x">${xfer.length} · ${xfer.every(h => h.term && +h.year) ? 'before Cal Poly' : 'AP, test and transfer credit'}</span></span></span>${pcChev(xOpen ? 90 : 0)}</button>${xOpen ? `<div class="pc-tlb">${xfer.map(trow).join('')}</div>` : ''}</div>` : '';
  const uCard = undated.length ? `<div class="card pc-ty"><div class="pc-th">NO TERM ON RECORD</div><div class="pc-tlb">${undated.map(trow).join('')}</div></div>` : '';
  return `<div class="pc-tv"><div class="pc-tvh"><button class="iconbtn" data-a="pcTerms" aria-label="Back to Past classes">${ic('chevL', 20, 2.6)}</button><h2>Every class, by term</h2></div><div class="pc-tls">${html}</div>${xCard}${uCard}</div>`;"""
s = s[:i] + NEW_TAIL + s[j2:]
# the old per-year chips and row: the timeline's rows read as words now (trow)
ci = s.index("  const chip = b => {\n    const g = pcGroupOf(b), lab = String(b.label || '');")
cj = s.index("  /* (2026-10-12, Tate's option B) a timeline")
s = s[:ci] + s[cj:]
# actions
rep("""  pcTerms: () => { UI.pcTerms = !UI.pcTerms; render(); },""", """  pcTerms: () => { UI.pcTerms = !UI.pcTerms; render(); },
  pcTermOpen: k => { UI.pcTermOpen = UI.pcTermOpen || {}; const cur = document.querySelector(`[data-a="pcTermOpen"][data-x="${CSS.escape(k)}"]`); UI.pcTermOpen[k] = !(cur && cur.getAttribute('aria-expanded') === 'true'); render(true); },
  pcTermOld: () => { UI.pcTermOld = true; render(true); },""")
p.write_text(s)
print('past-classes-a: applied')
