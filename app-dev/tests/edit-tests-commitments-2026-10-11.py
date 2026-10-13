#!/usr/bin/env python3
"""Tests for commitments-2026-10-11.py (work & activities). Run AFTER edit-harness-commitments-2026-10-11.py.
Usage: python3 edit-tests-commitments-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", r"""
/* (2026-10-11) Work & activities: asked before the Builder drafts; one entry on My Classes and every plan; Busy to friends */
tests.workActivities = async () => {
  let { page, close, log } = await openApp({ tables: NOPLANS(), cmAsked: false, height: 1400 });
  await toPlanner(page); await tick(page, 1500);
  const a0 = await page.evaluate(() => ({ ask: !!document.querySelector('#scroll .cm-ask'), wait: !!document.querySelector('#scroll .cm-wait'), drafted: !!plDrafted().at, plans: AT_PLANS.map(k => (TC.plans[k] || []).length).join(),
    picks: [...document.querySelectorAll('#scroll .cm-ask [data-a="cmAdd"]')].map(b => b.dataset.x + ':' + b.textContent.trim()), skip: (document.querySelector('#scroll .cm-skip') || {}).textContent }));
  ok(a0.ask && a0.wait && !a0.drafted && a0.plans === '0,0,0', 'work: before Plans A, B and C first draft, the Builder asks about work and practice — nothing drafts yet', a0);
  ok(a0.picks.join('|') === 'work:Work|practice:Practice|club:Club|other:Something else' && a0.skip === 'Skip', 'work: Work · Practice · Club, Something else, Skip', a0.picks);
  const row3 = await page.evaluate(() => { const b = [...document.querySelectorAll('#scroll .cm-ask .cm-pick')].map(x => x.getBoundingClientRect()); return { same: Math.abs(b[0].top - b[1].top) < 1 && Math.abs(b[1].top - b[2].top) < 1, under: b[3].top > b[0].bottom, wide: b[3].width > b[0].width * 2.5 }; });
  ok(row3.same && row3.under && row3.wide, 'work: Work, Practice and Club on one line; Something else across the card under them', row3);
  await click(page, '#scroll [data-a="cmAdd"][data-x="work"]'); await tick(page, 300);
  const sh = await page.evaluate(() => ({ t: document.querySelector('#sheet h3').textContent, kinds: /What is it|Every week/i.test(document.getElementById('sheet').innerText), name: document.getElementById('cm-name').value, on: !!document.querySelector('#sheet [data-a="cmBusy"].on') }));
  ok(sh.t === 'Add work' && !sh.kinds && sh.name === 'Work' && sh.on, 'work: the sheet is “Add work” — the kind isn’t asked again, no “every week” line; Friends see you’re busy is on', sh);
  await click(page, '#sheet [data-a="cmSave"]'); await tick(page, 200);
  ok(/Pick at least one day/.test(await page.locator('#sheet').innerText()), 'work: Save with no day says what’s missing');
  await page.fill('#cm-name', 'Barista shift');
  await click(page, '#sheet [data-a="cmDay"][data-x="T"]'); await click(page, '#sheet [data-a="cmDay"][data-x="R"]');
  /* the name typed survives the redraws the day taps make */
  ok(await page.evaluate(() => document.getElementById('cm-name').value) === 'Barista shift', 'work: what you typed stays as you tap days');
  await page.fill('#cm-from', '16:00'); await page.fill('#cm-to', '15:00'); await click(page, '#sheet [data-a="cmSave"]'); await tick(page, 200);
  ok(/end after it starts/.test(await page.locator('#sheet').innerText()), 'work: an end before the start is caught');
  await page.fill('#cm-to', '20:00'); await click(page, '#sheet [data-a="cmSave"]'); await tick(page, 2500);
  const w = log.writes.filter(x => x.table === 'commitments');
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.user_id === FX.ME.id && w[0].body.kind === 'work' && w[0].body.name === 'Barista shift' && w[0].body.days === 'TR' && w[0].body.start_min === 960 && w[0].body.end_min === 1200 && w[0].body.busy === true && /^[0-9a-f-]{36}$/.test(w[0].body.id), 'work: saved as one row — kind, name, days, start, end, Busy', w.map(x => x.body));
  const toastT = await page.evaluate(() => document.getElementById('toast').textContent);
  ok(toastT === 'Barista shift added to My Classes and Plans A, B and C', 'work: “Barista shift added to My Classes and Plans A, B and C”', toastT);
  const d = await page.evaluate(() => { const P = k => (TC.plans[k] || []).map(id => SEC[id]).filter(Boolean);
    return { drafted: !!plDrafted().at, n: AT_PLANS.map(k => P(k).length), clash: AT_PLANS.some(k => P(k).some(s => TC.commits.some(c => secClash(s, c)))), ask: !!document.querySelector('#scroll .cm-ask'), clear: (document.querySelector('#scroll .pl-clear') || {}).textContent || '' }; });
  ok(d.drafted && d.n.every(n => n > 0) && !d.clash && !d.ask, 'work: then Plans A, B and C draft — none over the shift', d);
  ok(d.clear === 'Clear of your work', 'work: the Builder says “Clear of your work”', d.clear);
  /* a new one over a drafted class: the plans still as drafted re-draft around it */
  const s0 = await page.evaluate(() => { const s = (TC.plans.A || []).map(id => SEC[id]).find(x => x && x.s != null && !x.async); return s && { days: s.days, s: s.s, e: s.e }; });
  await click(page, '#scroll .pl-clear'); await tick(page, 300);
  await click(page, '#sheet [data-a="cmAdd"][data-x="practice"]'); await tick(page, 300);
  for (const dd of s0.days) { await click(page, `#sheet [data-a="cmDay"][data-x="${dd}"]`); }
  const hm = m => String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');
  await page.fill('#cm-from', hm(s0.s)); await page.fill('#cm-to', hm(s0.e)); await click(page, '#sheet [data-a="cmSave"]'); await tick(page, 2500);
  const rd = await page.evaluate(() => ({ n: TC.commits.length, clash: AT_PLANS.some(k => (TC.plans[k] || []).map(id => SEC[id]).filter(Boolean).some(s => TC.commits.some(c => secClash(s, c)))), clear: (document.querySelector('#scroll .pl-clear') || {}).textContent || '' }));
  ok(rd.n === 2 && !rd.clash && /^Clear of your (work and practice|practice and work)$/.test(rd.clear), 'work: a new one over a drafted class — the plans re-draft around it (“Clear of your work and practice”)', rd);
  /* a section over the shift is never drafted: give a pick only a Tue/Thu 4:10p section, redraft */
  const cl = await page.evaluate(() => { plSync(); const L = TCPL.ledger(), R = planRank(L), c = R.all[0], base = secsOf(c.code)[0];
    const only = Object.assign({}, base, { id: '99400', sec: '07', days: 'TR', s: 970, e: 1050 }); SECS_BY_CODE[c.code] = [only]; SEC[only.id] = only;
    return { pick: plDraftSec(c.code, [], new Set()), code: c.code }; });
  ok(cl.pick === undefined || cl.pick === null, 'work: a class whose only section is over your shift is never drafted', cl);
  await page.evaluate(() => location.reload()); await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 10000 });
  /* My Classes */
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]'); await tick(page, 600);
  const m = await page.evaluate(() => ({ blocks: [...document.querySelectorAll('#scroll .g-cm')].map(b => b.textContent + '|' + b.dataset.a), tue: [...document.querySelectorAll('#scroll .mine-ag .ag-h')].map(h => h.innerText.replace(/\s+/g, ' ')) }));
  ok(m.blocks.filter(b => b === 'Barista shift|cmOpen').length === 2 && m.blocks.every(b => /\|cmOpen$/.test(b)), 'work: My Classes draws it on Tuesday and Thursday, by name', m);
  ok(m.tue.some(t => /^Tuesday.*Barista shift/.test(t)), 'work: the day card says so (“… · Barista shift”)', m.tue);
  await page.evaluate(() => { UI.agOpen = UI.agOpen || {}; document.querySelectorAll('.ag-fold .ag-h').forEach(b => { UI.agOpen[b.dataset.x] = true; }); render(true); }); await tick(page, 200);
  const rowT = await page.evaluate(() => { const r = [...document.querySelectorAll('#scroll .mine-ag .cm-row')].find(x => /Barista/.test(x.innerText)); return r && r.innerText.replace(/\s+/g, ' '); });
  ok(/^4p 8p Barista shift Friends see Busy$/.test(rowT || ''), 'work: an open day lists it in time order', rowT);
  /* every plan */
  await click(page, '[data-a="schedTab"][data-x="plans"]');
  const pl = [];
  for (const k of ['A', 'B', 'C']) { await click(page, `.seg.plans [data-a="pickPlan"][data-x="${k}"]`); await tick(page, 200); pl.push(await page.locator('#scroll .g-cm').count()); }
  ok(pl.every(n => n === m.blocks.length && n >= 2), 'work: every plan shows them too', pl);
  /* edit it, then remove it */
  await page.evaluate(() => [...document.querySelectorAll('#scroll .g-cm')].find(b => b.textContent === 'Barista shift').click()); await tick(page, 300);
  ok(await page.evaluate(() => document.querySelector('#sheet h3').textContent) === 'Edit Barista shift', 'work: tapping it opens it to edit');
  await click(page, '#sheet [data-a="cmDrop"]'); await tick(page, 600);
  ok(log.writes.some(x => x.table === 'commitments' && x.m === 'DELETE') && await page.locator('#scroll .g-cm').count() < m.blocks.length, 'work: Remove takes it off');
  ok(log.errors.length === 0, 'work: no page errors', log.errors);
  await close();
  /* Skip */
  ({ page, close, log } = await openApp({ tables: NOPLANS(), cmAsked: false }));
  await toPlanner(page); await tick(page, 1200);
  await click(page, '#scroll [data-a="cmSkip"]'); await tick(page, 1500);
  const sk = await page.evaluate(() => ({ ask: !!document.querySelector('#scroll .cm-ask'), drafted: !!plDrafted().at, clear: !!document.querySelector('#scroll .pl-clear') }));
  ok(!sk.ask && sk.drafted && !sk.clear, 'work: Skip — the plans draft, nothing to keep clear', sk);
  await close();
  /* your ring, a friend's Busy (never the name), and before RUN 18 (no table) */
  const fr = FX.FRIENDS[0].id;
  ({ page, close, log } = await openApp({ rpc: Object.assign({}, FX.RPC, { friend_busy_blocks: [{ user_id: fr, days: 'MTWRF', start_min: 0, end_min: 1439 }] }),
    hook: (url) => url.pathname.endsWith('/commitments') ? { status: 404, body: JSON.stringify({ code: 'PGRST205', message: "Could not find the table 'public.commitments' in the schema cache" }) } : null }));
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(page, 600);
  const st = await page.evaluate(async () => { const now = CLOCK.min;
    const err = await TC.saveCommit({ id: 'c-1', kind: 'practice', name: '', days: 'MTWRF', s: Math.max(0, now - 10), e: Math.min(1440, now + 50), busy: true });
    let kept = null; try { kept = JSON.parse(localStorage.getItem('tc-commits:' + TC.user.id)); } catch (e) {}
    const me = status('me'); return { err, missing: TC.err.commits, kept: kept && kept.length, me: me.t, free: me.free }; });
  ok(st.err === null && st.missing === 'missing' && st.kept === 1, 'work: before RUN 18 it’s kept on this phone, no error', st);
  ok(/^Practice till /.test(st.me) && st.free === false, 'work: your ring says “Practice till …”, never free', st);
  const fs = await page.evaluate(id => ({ t: status(id).t, free: status(id).free }), fr);
  ok(/^Busy till /.test(fs.t) && fs.free === false, 'work: a friend in their Busy time is “Busy till …” — never what it is', fs);
  ok(log.errors.length === 0, 'work: no page errors (friend and no-table)', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("work: the Builder drafts before asking", "  if (asked && data && UI.pl.prereqs !== false", "  if (data && UI.pl.prereqs !== false", "workActivities", None),
  ("work: no ask card", "  ${asked ? '' : cmAskCard()}", "  ${''}", "workActivities", None),
  ("work: a draft may sit over your shift", " && !TC.commits.some(t => secClash(s, t)));", ");", "workActivities", None),
  ("work: My Classes doesn't draw it", "grid(timed, Object.assign({ extra: cmBlocks('me') }, o.grid))", "grid(timed, Object.assign({ extra: [] }, o.grid))", "workActivities", None),
  ("work: plans don't draw it", "faces: true, extra: cmBlocks('me') })", "faces: true, extra: [] })", "workActivities", None),
  ("work: the day card leaves it out", "'mine-ag', () => cmMix(list, d, row).join(''), cmDayWords(d))", "'mine-ag', () => list.map(s => row(s)).join(''), '')", "workActivities", None),
  ("work: never saved to the server", "      : await TC.client().from('commitments').upsert(", "      : await TC.client().from('commitments_x').upsert(", "workActivities", None),
  ("work: Busy off by default", "name: CM_KINDS[k] || '', days: '', from: '', to: '', busy: true,", "name: CM_KINDS[k] || '', days: '', from: '', to: '', busy: false,", "workActivities", None),
  ("work: a friend's Busy shows the name", "label: 'Busy', mine: false", "label: 'Practice', mine: false", "workActivities", None),
  ("work: your ring says free in a shift", "  if (inc && inc.busy) return {", "  if (false) return {", "workActivities", None),
  ("work: no times check", "e <= s ? 'It has to end after it starts.' : null;", "null;", "workActivities", None),
  ("work: Skip never answers", "  cmSkip: () => { cmAskedSet(); render(true); },", "  cmSkip: () => { render(true); },", "workActivities", None),
  ("work: saved but plans not redrafted", "    UI.sheet = null; UI.plRefresh = true; render(true);\n    toast(err || (isNew", "    UI.sheet = null; render(true);\n    toast(err || (isNew", "workActivities", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
T = T.replace(k, "\n  /* work & activities (2026-10-11; edit-tests-commitments-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
# older mutants of lines this patch extended: the same mutation on the new words
RE = [
  ("\"  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return\", \"  if (!nowSecs(id).length && !nowUnplaced(id).length) return\"", "\"  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null) && !cmBlocks(id).length) return\", \"  if (!nowSecs(id).length && !nowUnplaced(id).length && !cmBlocks(id).length) return\""),
  ("\"  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return\", \"  if (!nowSecs(id).some(x => !x.async)) return\"", "\"  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null) && !cmBlocks(id).length) return\", \"  if (!nowSecs(id).some(x => !x.async) && !cmBlocks(id).length) return\""),
  ("\"  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return\", \"  if (!nowSecs(id).every(x => !x.async && x.s != null && x.e != null)) return\"", "\"  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null) && !cmBlocks(id).length) return\", \"  if (!nowSecs(id).every(x => !x.async && x.s != null && x.e != null) && !cmBlocks(id).length) return\""),
  ("\"  if (data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\", \"  if (UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\"", "\"  if (asked && data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\", \"  if (asked && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\""),
  ("\"  if (data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\", \"  if (data && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\"", "\"  if (asked && data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\", \"  if (asked && data && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);\""),
  ("\"margin:10px 12px 0;padding:14px 0 12px\\\">${grid(timed, o.grid)}\", \"margin:10px 16px 0;padding:14px 0 12px\\\">${grid(timed, o.grid)}\"", "\"margin:10px 12px 0;padding:14px 0 12px\\\">${grid(timed, Object.assign(\", \"margin:10px 16px 0;padding:14px 0 12px\\\">${grid(timed, Object.assign(\""),
  ("\" shared, one: true, fit: 30, H: 300 }) + (/^[ABC]$/.test(v.k) ? '</div>' : '') + anyRow;\", \" shared, one: true, fit: 30, H: 300 }) + (/^[ABC]$/.test(v.k) ? '</div>' : '');\"", "\" cmBlocks(isMe ? 'me' : id) }) + (/^[ABC]$/.test(v.k) ? '</div>' : '') + anyRow;\", \" cmBlocks(isMe ? 'me' : id) }) + (/^[ABC]$/.test(v.k) ? '</div>' : '');\""),
  ("\"key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300 })\", \"key: id, blockAct: 'secSheet', shared, one: true, H: 300 })\"", "\"key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300, extra:\", \"key: id, blockAct: 'secSheet', shared, one: true, H: 300, extra:\""),
  ("\"gridSpan(secs, o.fit ? 180 : 360)\", \"gridSpan(secs, 360)\"", "\"gridSpan(ex.length ? secs.concat(ex) : secs, o.fit ? 180 : 360)\", \"gridSpan(ex.length ? secs.concat(ex) : secs, 360)\""),
  ("\"const k = scope + ':' + d, open = !!UI.agOpen[k];\", \"const k = scope + ':' + d, open = Object.values(UI.agOpen).some(Boolean);\"", "\"const k = scope + ':' + d, open = !!UI.agOpen[k], lab\", \"const k = scope + ':' + d, open = Object.values(UI.agOpen).some(Boolean), lab\""),
  ("\"const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id] && !(have || []).some(t => secClash(s, t)));\", \"const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id]);\"", "\"SEC[s.id] && !(have || []).some(t => secClash(s, t)) && !TC.commits\", \"SEC[s.id] && !TC.commits\""),
]
for a, b in RE:
    if T.count(a) != 1: sys.exit('reaim ' + a[:70] + f' {T.count(a)}x')
    T = T.replace(a, b)
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-commitments: done')
