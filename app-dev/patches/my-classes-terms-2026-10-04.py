#!/usr/bin/env python3
r"""My Classes gets term chips — Fall 2026 · Spring 2027 — like Plans' A · B · C (Tate, 2026-10-04).

  "for my classes we need to make something similar to how plans has plan A,B,C but instead its Fall
  2026, Spring 2027 little bubbles because once theyve made the plan we want people to upload my
  classes spring 2027 when theyre silidified and actually gotten."

  · CFG.MY_TERMS lists the chips, in order. A term whose code is still '' (Spring 2027, until the
    Oct 5 discover_term run confirms it) shows its chip and reads NOTHING — never a guessed code.
    The entry whose label is TERM_LABEL always uses TERM, so the Oct 5 flip of TERM/TERM_LABEL to
    Spring fills Spring's code by itself, and Fall becomes the other chip.
  · The chip for TERM is My Classes exactly as before (Share, friends' faces, cards).
  · Another term is read from the student's own rows only (saved_classes + my_sections at that
    term). This term's seat feed is never asked about it: a class number names a different section
    in a different term. Its week has no "now" line or live block, and no Share (the share card is
    this term's).
  · The term bar loses "Fall 2026" (the chip says it); Share stays on the far right.

Usage: python3 my-classes-terms-2026-10-04.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

# 1. the chips, in config
rep("  REGISTRATION_TERM: 'Spring 2027',\n",
    "  REGISTRATION_TERM: 'Spring 2027',\n"
    "  /* My Classes' term chips, in order (2026-10-04). A code left '' shows the chip and reads nothing —\n"
    "     never guess one (see the desktop's note on TERM). The entry named TERM_LABEL always uses TERM,\n"
    "     so moving TERM/TERM_LABEL to Spring fills Spring's code here too. */\n"
    "  MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '', label: 'Spring 2027' }],\n")

# 2. state: the chosen chip survives closing the app
rep("plan: 'A', schedTab: 'mine', schedDay: null,", "plan: 'A', schedTab: 'mine', schedDay: null, mineTerm: null,")
rep("['exMode', 'subj', 'openOnly', 'saved', 'plan', 'schedTab', 'notifSeen']", "['exMode', 'subj', 'openOnly', 'saved', 'plan', 'schedTab', 'notifSeen', 'mineTerm']")
rep("plan: S.plan, schedTab: S.schedTab, notifSeen: S.notifSeen }", "plan: S.plan, schedTab: S.schedTab, notifSeen: S.notifSeen, mineTerm: S.mineTerm }")

# 3. reads for another term (a refresh drops what was read, so it is read again)
rep("async function loadMine() {\n",
    """/* ---- My Classes in another term (2026-10-04) ---- */
function myTerms() {
  const list = (Array.isArray(CFG.MY_TERMS) ? CFG.MY_TERMS : []).map(t => ({ code: t && t.label === CFG.TERM_LABEL ? CFG.TERM : String((t && t.code) || '').trim(), label: String((t && t.label) || '') })).filter(t => t.label);
  if (!list.some(t => t.code === CFG.TERM)) list.unshift({ code: CFG.TERM, label: CFG.TERM_LABEL });
  return list;
}
function mineTerm() { const L = myTerms(); return L.find(t => t.label === S.mineTerm) || L.find(t => t.code === CFG.TERM); }
TC.termMine = {}; TC.termGen = 0;
async function loadTermMine(code) {
  if (!code || code === CFG.TERM || !TC.user) return;
  const box = TC.termMine[code]; if (box && (box.loading || box.rows)) return;
  TC.termMine[code] = { loading: true };
  const sb = TC.client(), me = TC.user.id, gen = TC.termGen;
  let codes, secs;
  try {
    [codes, secs] = await Promise.all([
      sb.from('saved_classes').select('code').eq('user_id', me).eq('term', code),
      sb.from('my_sections').select('code,class_nbr,section,instructor,days,status').eq('user_id', me).eq('term', code)
    ]);
  } catch (e) { codes = { error: { message: String(e) } }; }
  if (gen !== TC.termGen) return;   /* a refresh started over meanwhile; its own read wins */
  const bad = codes.error || (secs && secs.error);
  TC.termMine[code] = bad ? { err: bad.message || 'error' }
    : { rows: (secs && !secs.error && secs.data) || [], saved: [...new Set((codes.data || []).map(r => canonCode(r.code)).filter(Boolean))] };
  render(true);
}
/* Another term's classes from the student's own rows alone. This term's seat feed (SEC) is never
   consulted: the same class number is a different section in a different term. */
function termSecs(code) {
  const box = TC.termMine[code]; if (!box || !box.rows) return null;
  const out = [], keep = new Set(box.saved), unplaced = [];
  box.rows.forEach(r => {
    const c = canonCode(r.code); if (!c || !keep.has(c)) return;
    const m = parseMeet(r.days); if (!m) return;
    const pk = profKeyOf(r.instructor); if (pk) ensureProf(pk);
    out.push({ id: 't:' + code + ':' + c + ':' + (r.class_nbr == null ? '' : r.class_nbr), code: c, sec: r.section || '', prof: pk, days: m.days, s: m.s, e: m.e, async: false, seats: null, status: 'unknown', offFeed: true });
  });
  keep.forEach(c => { if (!out.some(x => x.code === c)) unplaced.push(c); });
  return { secs: out, unplaced };
}
async function loadMine() {
  TC.termMine = {}; TC.termGen++;
""")

# 4. a week with no "now": another term's grid
rep("  const today = CLOCK.day, nowMin = CLOCK.min;", "  const today = o.noNow ? '' : CLOCK.day, nowMin = CLOCK.min;")

# 5. actions
rep("  pickPlan: k => { S.plan = k; save(); render(true); },",
    "  pickPlan: k => { S.plan = k; save(); render(true); },\n"
    "  /* the current term is stored as null, so after the Oct 5 flip nobody is left on last term's chip */\n"
    "  pickMineTerm: k => { const t = myTerms().find(x => x.label === k); S.mineTerm = t && t.code !== CFG.TERM ? k : null; S.schedDay = null; save(); render(true); },\n"
    "  mineTermRetry: () => { const t = mineTerm(); if (t && t.code) { delete TC.termMine[t.code]; render(true); } },")

# 6. the screen
rep("""    inner = `<div class="regbar" style="margin-top:14px"><span>${esc(CFG.TERM_LABEL)}</span><button class="shbtn" data-a="shareOpen" data-x="mine" aria-label="Share your week" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>
  ${TC.err.mine""",
    """    const terms = myTerms(), tm = mineTerm();
    const chips = `<div class="pad" style="margin-top:14px"><div class="seg terms" role="group" aria-label="Term">${terms.map(x => `<button class="${x.label === tm.label ? 'on' : ''}" data-a="pickMineTerm" data-x="${esc(x.label)}" aria-pressed="${x.label === tm.label}">${esc(x.label)}</button>`).join('')}</div></div>`;
    if (tm.code !== CFG.TERM) inner = chips + otherTermMine(terms, tm);
    else inner = chips + `<div class="regbar" style="justify-content:flex-end"><button class="shbtn" data-a="shareOpen" data-x="mine" aria-label="Share your week" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>
  ${TC.err.mine""")

rep("/* ---- Schedule --------------------------------------------------------------------------------- */\n",
    """/* ---- Schedule --------------------------------------------------------------------------------- */
/* My Classes on a term chip that isn't TERM: read-only, from the student's own rows. */
function otherTermMine(terms, tm) {
  const L = esc(tm.label);
  if (!tm.code) return `<div class="empty" style="margin-top:6px"><b>${L} isn’t posted yet</b>Once Cal Poly posts the ${L} schedule and you’ve registered, your ${L} classes go here.</div>`;
  const box = TC.termMine[tm.code];
  if (!box) { loadTermMine(tm.code); return loadingCard('Loading your ' + tm.label + ' classes…'); }
  if (box.loading) return loadingCard('Loading your ' + tm.label + ' classes…');
  if (box.err) return errCard('Couldn’t load your ' + tm.label + ' classes.', 'mineTermRetry');
  const ts = termSecs(tm.code), later = terms.findIndex(x => x.label === tm.label) > terms.findIndex(x => x.code === CFG.TERM);
  if (!ts.secs.length && !ts.unplaced.length) return `<div class="empty" style="margin-top:6px"><b>No ${L} classes yet</b>${later ? `Once you’ve registered, import your ${L} schedule on ${webLink('termchamp.com', '/')} and it shows up here.` : `There are no ${L} classes on your account.`}</div>`;
  const byCode = {}; ts.secs.forEach(x => { (byCode[x.code] = byCode[x.code] || []).push(x); });
  const name = code => courseName(code) || course(code).title;
  return `${ts.secs.length ? `<div class="card" style="margin:10px 12px 0;padding:14px 0 12px">${grid(ts.secs, { sel: S.schedDay, act: 'schedDay', blockAct: 'openClass', H: 330, noNow: true })}</div>` : ''}
  ${Object.keys(byCode).map(code => { const ss = byCode[code]; return `<button class="card ccard" style="margin:12px 12px 0;width:calc(100% - 24px)" data-a="openClass" data-x="${code}">
   <div class="row sb"><span class="code">${code}</span>${ss[0].sec ? `<span class="muted b" style="font-size:13px">${esc(secLabel(ss[0].sec))}</span>` : ''}</div>
   <div class="ctitle" style="margin:8px 0 4px">${esc(name(code))}</div>
   ${ss.map(x => `<div class="muted b" style="font-size:14px">${esc(profName(x.prof))} · ${secWhen(x)}</div>`).join('')}</button>`; }).join('')}
  ${ts.unplaced.map(code => `<button class="card ccard" style="margin:12px 12px 0;width:calc(100% - 24px)" data-a="openClass" data-x="${code}"><div class="row sb"><span class="code">${code}</span><span class="muted b" style="font-size:13px">${(TC.termMine[tm.code].rows || []).some(r => canonCode(r.code) === code) ? 'No set time' : 'No section yet'}</span></div><div class="ctitle" style="margin:8px 0 0">${esc(name(code))}</div></button>`).join('')}`;
}
""")

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
