#!/usr/bin/env python3
"""The report wins over what's on your account (Tate, 2026-10-11).

Tate's account showed BUS 3431 under Fall 2025 (he's taking it now), BUS 3440 in progress (never taken), and
BUS 4446 as transfer credit (not on his report): rows older imports wrote. Saving a report only ever ADDED rows,
so a new report could never fix them — and the reader called a class "already on your record" by its number alone,
so the BUS 3431 he's taking was skipped because of the wrong Fall 2025 row.

- "Already on your record" now means the same class in the same term (a row with no term: the same class).
- Report read lists what's on your account but not on your report — past classes, credit, and (when the report
  shows this term) this term's My Classes — each with why, checked; "See my plan" takes the checked ones off
  first, so your account matches your report. Uncheck one to keep it.
- Every class, by term: credit posted after your first Cal Poly term (study abroad, a summer elsewhere) sits in
  that term, marked "Other school"; only credit from before Cal Poly sits apart ("Credit from other schools").
Usage: python3 dpr-report-wins-2026-10-11.py <repo-dir>   (replayable on build 22:18 + 3f41a64)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)

rep(".dr-foot{display:flex;flex-direction:column;gap:8px}", """.dr-foot{display:flex;flex-direction:column;gap:8px}
/* what's on your account but not on your report (2026-10-11) */
.dr-rc{background:var(--card);border-radius:20px;padding:14px 14px 8px;margin:0 0 14px;box-shadow:inset 0 0 0 2px var(--amber-wash)}
.dr-rch{font-size:16px;font-weight:900}
.dr-rcs{font-size:13px;font-weight:700;color:var(--muted);line-height:1.45;margin:4px 0 8px}
.dr-rcr{display:flex;align-items:flex-start;gap:12px;width:100%;padding:10px 0;border-top:1px solid var(--line);text-align:left;min-height:48px}
.dr-rcb{width:22px;height:22px;flex:none;border-radius:7px;display:grid;place-items:center;box-shadow:inset 0 0 0 2px var(--ink5,var(--muted));color:#fff;margin-top:1px}
.dr-rcr[aria-pressed="true"] .dr-rcb{background:var(--blue);box-shadow:none}
.dr-rct{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.dr-rct b{font-size:15px;font-weight:900}
.dr-rct span{font-size:13px;font-weight:800;color:var(--muted)}""", 'css')

# already = the same class in the same term; then what's on the account but not on the report
rep("""    if (x._now && nowCodes().has(x.cur)) { x.already = true; x.pick = false; }
    if (x._next && planCodes().has(x.cur)) { x.already = true; x.pick = false; }
  });
  r.latestTerm = nt.label; r.nextTerm = splitTerms() ? CFG.TERM_LABEL : '';""", """    if (x._now && nowCodes().has(x.cur)) { x.already = true; x.pick = false; }
    if (x._next && planCodes().has(x.cur)) { x.already = true; x.pick = false; }
  });
  dprRecompute(r); r.rc = dprStale(r); r.rcOff = new Set();
  r.latestTerm = nt.label; r.nextTerm = splitTerms() ? CFG.TERM_LABEL : '';""", 'read post')

rep("""/* ================= screens ================= */
function meBtn() {""", """/* (2026-10-11) "Already on your record" = the same class in the same term (or a row with no term). By number alone, a
   wrong row from an older import (BUS 3431 under Fall 2025) hid the class you're taking now. A row the student unpicked
   or flagged stays as they left it. */
function dprRecompute(r) {
  const K = c => pcK(c), now = new Set([...nowCodes()].map(K)), plan = planCodes();
  r.rows.forEach(x => {
    if (x.flag || x.skip || x.unpicked) return;
    if (x._now) x.already = now.has(K(x.cur));
    else if (x._next) x.already = plan.has(x.cur);
    else x.already = (TC.myHistory || []).some(h => (K(h.code) === K(x.cur) || K(h.code) === K(x.code)) && (!h.term || !h.year || (h.term === x.term && String(h.year) === String(x.year))));
    x.pick = !x.already;
  });
}
/* What's on your account but not on your report: the report decides, so these come off when you save — unless you
   uncheck them. This term's My Classes only when the report shows this term (it lists what you're taking). */
function dprStale(r) {
  const K = c => pcK(c), rows = r.rows || [];   // any row on the report, flagged or later-term too, keeps its class
  const same = (x, h) => K(x.cur) === K(h.code) || K(x.code) === K(h.code);
  const out = [];
  (TC.myHistory || []).forEach(h => {
    /* a row with no term the report dates (credit an older import wrote undated) comes off too: it's saved again with its term */
    if (rows.some(x => same(x, h) && (h.term && h.year ? x.term === h.term && String(x.year) === String(h.year) : !(x.term && x.year)))) return;
    const other = rows.find(x => same(x, h)), at = h.term && h.year ? `as ${h.term} ${h.year}` : 'with no term';
    const why = other ? `On your account ${at} · your report has it ${other.term} ${other.year}${other._now ? ' (this term)' : ''}` : pcXfer(h) ? 'Credit on your account · not on your report' : `On your account ${at} · not on your report`;
    out.push({ key: 'h:' + pcKey(h), kind: 'hist', h, code: K(h.code), why });
  });
  const nowRep = rows.filter(x => x._now);
  if (nowRep.length) {
    const want = new Set(nowRep.map(x => K(x.cur)));
    [...nowCodes()].map(K).filter((c, i, a) => a.indexOf(c) === i && !want.has(c)).forEach(c => out.push({ key: 'n:' + c, kind: 'now', code: c, why: `In My Classes for ${nowTerm().label} · your report doesn’t show you taking it` }));
  }
  return out;
}
function dprRcCard(r) {
  const rc = r.rc || []; if (!rc.length) return '';
  const off = r.rcOff || new Set(), n = rc.filter(x => !off.has(x.key)).length;
  return `<div class="dr-rc" role="group" aria-label="On your account, not on your report"><div class="dr-rch">${rc.length} on your account, not on your report</div><div class="dr-rcs">Your report decides. We’ll take the checked ${n === 1 ? 'one' : 'ones'} off so your account matches it.</div>${rc.map(x => { const on = !off.has(x.key); return `<button class="dr-rcr" data-a="dprRc" data-x="${esc(x.key)}" aria-pressed="${on}"><span class="dr-rcb" aria-hidden="true">${on ? ic('check', 14, 3.4) : ''}</span><span class="dr-rct"><b>${esc(x.code)}${courseName(x.code) ? ' · ' + esc(courseName(x.code)) : ''}</b><span>${esc(x.why)}</span></span></button>`; }).join('')}</div>`;
}
TC.dropStale = async function (list) {
  const sb = TC.client(), me = TC.user.id, nt = nowTerm().code;
  for (const x of list) {
    let q;
    if (x.kind === 'hist') { q = sb.from('class_history').delete().eq('user_id', me).eq('code', x.h.code); q = x.h.term == null ? q.is('term', null) : q.eq('term', x.h.term); q = x.h.year == null ? q.is('year', null) : q.eq('year', x.h.year); }
    else q = sb.from('saved_classes').delete().eq('user_id', me).eq('term', nt).eq('code', x.code);
    const d = await q;
    if (d.error) { await Promise.all([TC.reloadHistory(), loadMine()]); return dbSay(d.error, `Couldn’t take ${x.code} off your account.`); }
    if (x.kind === 'now') await sb.from('my_sections').delete().eq('user_id', me).eq('term', nt).eq('code', x.code);
  }
  await Promise.all([TC.reloadHistory(), loadMine()]);
  return null;
};

/* ================= screens ================= */
function meBtn() {""", 'helpers')

rep("""  ${r.saveErr ? `<div class="tc-err">${esc(r.saveErr)}</div>` : ''}
  <div class="dr-foot"><button class="btn" data-a="dprSave\"""", """  ${dprRcCard(r)}${r.saveErr ? `<div class="tc-err">${esc(r.saveErr)}</div>` : ''}
  <div class="dr-foot"><button class="btn" data-a="dprSave\"""", 'sheets', 2)

rep("""      r.rows.forEach(x => { if (x.flag) x.pick = false; });
      const e = await TC.saveDpr(r);""", """      r.rows.forEach(x => { if (x.flag) x.pick = false; });
      /* (2026-10-11) the report wins: what's on your account but not on it comes off first (unless unchecked) */
      const drop = (r.rc || []).filter(x => !(r.rcOff || new Set()).has(x.key));
      if (drop.length) { const e0 = await TC.dropStale(drop); if (e0) { r.saveErr = e0; return; } dprRecompute(r); r.rc = []; notes.push(`Took ${drop.length} off your account so it matches your report.`); }
      const e = await TC.saveDpr(r);""", 'save')

rep("""  dprSave: async () => {""", """  dprRc: key => { const r = UI.dpr; if (!r) return; r.rcOff = r.rcOff || new Set(); if (r.rcOff.has(key)) r.rcOff.delete(key); else r.rcOff.add(key); render(true); },
  dprSave: async () => {""", 'action')

# every class, by term: credit posted after your first Cal Poly term sits in that term
rep("""  const hist = pcHist(), xfer = hist.filter(pcXfer), real = hist.filter(h => !pcXfer(h) && h.term && +h.year);""",
    """  const hist = pcHist(), real0 = hist.filter(h => !pcXfer(h) && h.term && +h.year);
  /* (2026-10-11) credit posted after your first Cal Poly term (study abroad, a summer elsewhere) was earned then: it
     sits in that term, marked "Other school"; only credit from before Cal Poly sits apart */
  const tk = h => (+h.year) * 10 + ({ Winter: 1, Spring: 2, Summer: 3, Fall: 4 }[h.term] || 0), k0 = real0.length ? Math.min(...real0.map(tk)) : Infinity;
  const away = hist.filter(h => pcXfer(h) && h.term && +h.year && tk(h) > k0).map(h => Object.assign({}, h, { oth: true }));
  const xfer = hist.filter(h => pcXfer(h) && !(h.term && +h.year && tk(h) > k0)), real = real0.concat(away);""", 'terms split')
rep("""    const cf = (f && f.lines.length ? f.lines.map(chip).join('') : '') + (ip ? '<i class="c">In progress</i>' : f && !f.lines.length ? '<i class="u">Units only</i>' : '');""",
    """    const cf = (h.oth ? '<i class="d">Other school</i>' : '') + (f && f.lines.length ? f.lines.map(chip).join('') : '') + (ip ? '<i class="c">In progress</i>' : f && !f.lines.length ? '<i class="u">Units only</i>' : '');""", 'other school chip')
rep("""<b>Transfer and AP credit</b><span><span class="x">${xfer.length} · not tied to a term you took</span></span>""",
    """<b>Credit from other schools</b><span><span class="x">${xfer.length} · ${xfer.every(h => h.term && +h.year) ? 'before Cal Poly' : 'AP, test and transfer credit'}</span></span>""", 'credit label')
# this term's classes show unless your account has them in THIS term (a wrong older row of the same class hid them)
rep("""have = new Set((TC.myHistory || []).map(h => pcK(h.code)));""", """have = new Set((TC.myHistory || []).filter(h => h.term === nowT[0] && String(h.year) === nowT[1]).map(h => pcK(h.code)));""", 'now rows')
rep("if (x) x.pick = t.checked; render(true); return; }", "if (x) { x.pick = t.checked; x.unpicked = !t.checked; } render(true); return; }", 'unpick')
open(PA, 'w', encoding='utf-8').write(S); print('dpr-report-wins: done')
