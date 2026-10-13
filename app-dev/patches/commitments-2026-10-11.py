#!/usr/bin/env python3
r"""Work & activities: log work, practice, a club or anything else every week; it shows on My Classes, every plan, Home
and (as "Busy") to friends, and the Builder drafts around it (Tate, 2026-10-11: "put in place a simple way to log Work
and Extra curriculars like sports practice … so it can also be shown on schedules … before you make a schedule so you
could base your classes around this"; then "make sure when you fill something in like work or practice that it then
fills in for all plans and My Classes … work, practice and club all on the same line and then something else under it
… dont need to see the what is it again … dont add the every week this term"; canvas *Work & Activities*, with
Tate's own fixes, then "implement into app index html").

  · Builder: before Plans A, B and C first draft, "Before we build your plans" — Work · Practice · Club, Something
    else, Skip. Nothing drafts until it's answered (an Add or Skip); plans that already exist stay.
  · The sheet: "Add work" (the kind is the title, never asked again) — name (only you see it), days M–Su, From / To,
    "Friends see you're busy" (on), Save; editing adds Remove.
  · One entry, everywhere: hatched blocks on My Classes (both chips), every plan and your Home week; the day cards
    list it in time order ("2 classes · Work"); weekend times under the week. Saving says "… added to My Classes and
    Plans A, B and C", and plans still exactly as drafted re-draft around it.
  · The Builder never picks a section over one ("Clear of your work and practice" on the card; tap it to edit).
  · Your ring: "Barista shift till 8p", never "Free". A friend's Busy times (only items they left on, never the name)
    show as "Busy" on their week and ring — from friend_busy_blocks() (RUN 18, sql/professify-commitments.sql).
  · Before RUN 18 the phone keeps them, and they go up the first time the table answers.
Run AFTER builder-2026-10-11.py.  Usage: python3 commitments-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)

# ---------- data
rep("""function regFrRows() {""", r"""/* ================= work & activities (2026-10-11) =================
   TC.commits = [{ id, kind 'work'|'practice'|'club'|'other', name, days 'MTWRFSU', s, e (minutes), busy }] — yours,
   every week, from commitments (owner-only; RUN 18) or, before RUN 18, this phone. TC.frBusy = { [friend id]:
   [{ days, s, e }] } — friends' Busy times from friend_busy_blocks(): only items they left "Friends see you're busy"
   on, never the name or kind. One list, so one entry shows on My Classes, every plan and Home alike. */
const CM_KEY = () => 'tc-commits:' + ((TC.user && TC.user.id) || '');
const CM_ASK = () => 'tc-commits-asked:' + ((TC.user && TC.user.id) || '');
const CM_KINDS = { work: 'Work', practice: 'Practice', club: 'Club', other: '' };
const CM_ADD = { work: 'Add work', practice: 'Add practice', club: 'Add a club', other: 'Add something else' };
TC.commits = []; TC.frBusy = {};
const cmOk = x => !!x && /^[MTWRFSU]{1,7}$/.test(String(x.days || '')) && Number.isInteger(+x.s) && Number.isInteger(+x.e) && +x.s >= 0 && +x.e <= 1440 && +x.s < +x.e;
const cmLabel = x => String((x && x.name) || '').trim() || CM_KINDS[x && x.kind] || 'Busy';
const cmFromRow = r => ({ id: String(r.id), kind: r.kind in CM_KINDS ? r.kind : 'other', name: String(r.name || '').slice(0, 40), days: String(r.days || ''), s: +r.start_min, e: +r.end_min, busy: r.busy !== false });
const cmId = () => { try { if (crypto.randomUUID) return crypto.randomUUID(); } catch (e) {} return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16)); };
function cmKeep() { try { localStorage.setItem(CM_KEY(), JSON.stringify(TC.commits)); } catch (e) {} }
function cmAsked() { if (TC.commits.length) return true; try { return localStorage.getItem(CM_ASK()) === '1'; } catch (e) { return false; } }
function cmAskedSet() { try { localStorage.setItem(CM_ASK(), '1'); } catch (e) {} }
async function loadCommits() {
  delete TC.err.commits;
  let loc = []; try { loc = JSON.parse(localStorage.getItem(CM_KEY()) || '[]'); } catch (e) {}
  TC.commits = (Array.isArray(loc) ? loc : []).filter(cmOk);
  let r; try { r = await TC.client().from('commitments').select('id,kind,name,days,start_min,end_min,busy').eq('user_id', TC.user.id).order('start_min'); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.commits = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  const rows = (Array.isArray(r.data) ? r.data : []).map(cmFromRow).filter(cmOk);
  /* kept on this phone before RUN 18: the first time the table answers with nothing, they go up */
  if (!rows.length && TC.commits.length) { for (const x of TC.commits) await cmPush(x); return; }
  TC.commits = rows.sort((a, b) => a.s - b.s); cmKeep();
}
/* up to the server (gone: removes it). Returns what to tell the student, or null. */
async function cmPush(x, gone) {
  if (TC.err.commits === 'missing') return null;
  let q;
  try {
    q = gone ? await TC.client().from('commitments').delete().eq('id', x.id).eq('user_id', TC.user.id)
      : await TC.client().from('commitments').upsert({ id: x.id, user_id: TC.user.id, kind: x.kind, name: x.name || null, days: x.days, start_min: x.s, end_min: x.e, busy: !!x.busy }, { onConflict: 'id' });
  } catch (e) { q = { error: { message: String((e && e.message) || e) } }; }
  if (q.error) { if (schemaGap(q.error)) { TC.err.commits = 'missing'; return null; } return dbSay(q.error, 'Couldn’t save that — it’s kept on this phone for now.'); }
  return null;
}
TC.saveCommit = async function (x) {
  const i = TC.commits.findIndex(c => c.id === x.id); if (i >= 0) TC.commits[i] = x; else TC.commits.push(x);
  TC.commits.sort((a, b) => a.s - b.s); cmKeep(); cmAskedSet();
  return cmPush(x);
};
TC.dropCommit = async function (id) { const x = TC.commits.find(c => c.id === id); if (!x) return null; TC.commits = TC.commits.filter(c => c.id !== id); cmKeep(); return cmPush(x, true); };
async function loadFriendBusy() {
  let r; try { r = await Promise.race([TC.client().rpc('friend_busy_blocks'), new Promise((_, no) => setTimeout(() => no(new Error('timeout')), 10000))]); } catch (e) { r = { error: { message: String((e && e.message) || e) } }; }
  if (r.error) { TC.frBusy = {}; return; }
  const out = {};
  (Array.isArray(r.data) ? r.data : []).forEach(x => { if (!x || !x.user_id) return; const b = { days: String(x.days || ''), s: +x.start_min, e: +x.end_min }; if (cmOk(b)) (out[x.user_id] = out[x.user_id] || []).push(b); });
  TC.frBusy = out;
}
/* the blocks a week draws besides classes: yours by name (only you see them), a friend's as Busy */
function cmBlocks(id) {
  if (id === 'me' || (TC.user && id === TC.user.id)) return TC.commits.map(x => ({ id: x.id, days: x.days, s: x.s, e: x.e, label: cmLabel(x), mine: true }));
  return ((TC.frBusy || {})[id] || []).map((x, i) => ({ id: 'b' + i, days: x.days, s: x.s, e: x.e, label: 'Busy', mine: false }));
}
/* the words for a day card and the Builder's line: "Work", "Work · Practice" */
const cmDayWords = d => [...new Set(TC.commits.filter(x => x.days.includes(d)).map(cmLabel))].join(' · ');
function cmWords() {
  const w = [...new Set(TC.commits.map(x => x.kind === 'other' ? cmLabel(x).toLowerCase() : x.kind))];
  return w.length <= 2 ? w.join(' and ') : w.slice(0, -1).join(', ') + ' and ' + w[w.length - 1];
}
/* a day's classes and your times, in time order */
function cmMix(list, d, fn) {
  const cs = TC.commits.filter(x => x.days.includes(d)).map(x => ({ s: x.s, cm: x }));
  return list.map(s => ({ s: s.s, sec: s })).concat(cs).sort((a, b) => a.s - b.s).map(x => x.cm ? cmRow(x.cm) : fn(x.sec));
}
const cmRow = x => `<button class="arow cm-row" data-a="cmOpen" data-x="${esc(x.id)}"><span class="tm">${hs(x.s)}<small>${hs(x.e)}</small></span><span class="vb cm-vb"></span><span class="grow"><span style="font-weight:900;font-size:16px">${esc(cmLabel(x))}</span><span class="muted b" style="display:block;font-size:14px">${x.busy ? 'Friends see Busy' : 'Only you'}</span></span></button>`;
const cmDaysText = days => [...days].map(d => DAYN[d]).join(', ');
/* weekend times (the week has no Sat/Sun column) */
function cmWeekend() {
  const w = TC.commits.filter(x => /[SU]/.test(x.days)); if (!w.length) return '';
  return `<div class="cm-wkend"><span class="cm-sw" aria-hidden="true"></span>Weekend · ${w.map(x => `${esc([...x.days].filter(d => d === 'S' || d === 'U').map(d => DAYN[d]).join('/'))} ${esc(cmLabel(x))} ${hs(x.s)}–${hs(x.e)}`).join(' · ')}</div>`;
}
/* The Builder, before Plans A, B and C first draft */
function cmAskCard() {
  const b = (k, lab, ic2, wide) => `<button class="cm-pick${wide ? ' wide' : ''}" data-a="cmAdd" data-x="${k}">${ic2}${lab}</button>`;
  const sv = (p, c) => `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
  return `<div class="card tc-sec cm-ask"><div class="cm-askh"><span class="cm-ico" aria-hidden="true">${sv('<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>', 'var(--blue-ink)')}</span><span><b>Before we build your plans</b><span>Do you work, practice or have anything else every week? The Builder won’t put a class over it.</span></span></div>
  <div class="cm-picks">${b('work', 'Work', sv('<rect x="3" y="7" width="18" height="13" rx="2"></rect><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"></path>', 'var(--amber)'))}${b('practice', 'Practice', sv('<circle cx="12" cy="12" r="9"></circle><path d="M12 3v18M3 12h18"></path>', 'var(--green)'))}${b('club', 'Club', sv('<circle cx="9" cy="8" r="3.2"></circle><circle cx="17" cy="9" r="2.6"></circle><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M15 14.5c3 0 6 2 6 5.5"></path>', 'var(--purple)'))}${b('other', 'Something else', sv('<path d="M12 5v14M5 12h14"></path>', 'var(--blue-ink)'), true)}</div>
  <button class="cm-skip" data-a="cmSkip">Skip</button></div>`;
}
const cmWaitCard = k => `<div class="card pl-card pla plan-${k} cm-wait">${planTabs(k)}<div class="pl-rech cm-rech">Recommended for Plan ${k}</div><div class="pl-recs">Drafts once you’ve told us about your week</div></div>`;
function regFrRows() {""", 'data')
rep("""loadAudit(), loadPrefs(), loadRegDay()]);""", """loadAudit(), loadPrefs(), loadRegDay(), loadCommits(), loadFriendBusy()]);""", 'load')

# ---------- your day and a friend's: rings, the story order
rep("""function busyToday(id) { return todaySecs(id); }""",
    """function busyToday(id) {
  const t = todaySecs(id), d = CLOCK.day;
  /* (2026-10-11) work, practice and the rest fill the day too: yours by name, a friend's as Busy */
  const c = cmBlocks(id).filter(x => x.days.includes(d)).map(x => ({ code: x.label, s: x.s, e: x.e, days: x.days, busy: true }));
  return c.length ? t.concat(c).sort((a, b) => a.s - b.s) : t;
}""", 'busyToday')
rep("""  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return {""", """  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null) && !cmBlocks(id).length) return {""", 'status set time')
rep("""  if (inc) return { c: isDark() ? '#6EA2FF' : '#2563EB', t: `In ${inc.code} till ${hs(inc.e)}`, free: false };""",
    """  if (inc && inc.busy) return { c: isDark() ? '#8F9BAE' : '#64748B', t: `${inc.code} till ${hs(inc.e)}`, free: false };
  if (inc) return { c: isDark() ? '#6EA2FF' : '#2563EB', t: `In ${inc.code} till ${hs(inc.e)}`, free: false };""", 'status busy')

# ---------- the week grid draws them
rep("""  const [S0, S1] = gridSpan(secs, o.fit ? 180 : 360);
  const has = d => secs.some(s => timed(s) && s.days.includes(d));""",
    """  const ex = (o.extra || []).filter(x => x && x.s != null && x.e != null);
  const [S0, S1] = gridSpan(ex.length ? secs.concat(ex) : secs, o.fit ? 180 : 360);
  const has = d => secs.some(s => timed(s) && s.days.includes(d)) || ex.some(x => x.days.includes(d));""", 'grid span')
rep("""    return `<div class="g-col ${wide ? 'on' : ''}"${o.act ? ` data-a="${o.act}" data-x="${d}"${o.key != null ? ` data-y="${esc(o.key)}"` : ''}` : ''}>${blocks}${now}</div>`;""",
    """    /* (2026-10-11) work, practice and the rest: hatched, under the classes; yours open to edit, a friend's say Busy */
    const exB = ex.filter(x => x.days.includes(d)).map(x => { const top = Math.max(0, Y(x.s)), h = Math.max(14, Math.min(H + GPAD - top, (x.e - x.s) * k)), al = `${x.label}, ${DAYN[d]} ${hs(x.s)}–${hs(x.e)}`;
      return x.mine ? `<button class="g-cm" style="top:${top}px;height:${h}px" data-a="cmOpen" data-x="${esc(x.id)}" aria-label="${esc(al)}"><span>${esc(x.label)}</span></button>` : `<span class="g-cm fr" style="top:${top}px;height:${h}px" role="img" aria-label="${esc(al)}"><span>Busy</span></span>`; }).join('');
    return `<div class="g-col ${wide ? 'on' : ''}"${o.act ? ` data-a="${o.act}" data-x="${d}"${o.key != null ? ` data-y="${esc(o.key)}"` : ''}` : ''}>${exB}${blocks}${now}</div>`;""", 'grid blocks')

# My Classes (both chips)
rep("""  const days = DAYS.map(d => [d, timed.filter(s => String(s.days).includes(d)).sort((a, b) => a.s - b.s)]).filter(x => x[1].length);""",
    """  const days = DAYS.map(d => [d, timed.filter(s => String(s.days).includes(d)).sort((a, b) => a.s - b.s)]).filter(x => x[1].length || cmDayWords(x[0]));""", 'mine days')
rep("""'mine-ag', () => list.map(s => row(s)).join(''))).join('');""", """'mine-ag', () => cmMix(list, d, row).join(''), cmDayWords(d))).join('');""", 'mine rows')
rep("""  const week = timed.length ? `<div class="card" style="margin:10px 12px 0;padding:14px 0 12px">${grid(timed, o.grid)}</div>` : '';""",
    """  const week = timed.length || TC.commits.length ? `<div class="card" style="margin:10px 12px 0;padding:14px 0 12px">${grid(timed, Object.assign({ extra: cmBlocks('me') }, o.grid))}${cmWeekend()}</div>` : '';""", 'mine week')
rep("""  ${secs.length || unplaced.length ? mineAgenda(""", """  ${secs.length || unplaced.length || TC.commits.length ? mineAgenda(""", 'mine show')
# a day card says what's on it besides classes
rep("""function agCard(scope, d, n, today, cls, rows) {
  UI.agOpen = UI.agOpen || {};
  const k = scope + ':' + d, open = !!UI.agOpen[k];""", """function agCard(scope, d, n, today, cls, rows, more) {
  UI.agOpen = UI.agOpen || {};
  const k = scope + ':' + d, open = !!UI.agOpen[k], lab = [n ? `${n} class${n === 1 ? '' : 'es'}` : '', more || ''].filter(Boolean).join(' · ');""", 'agCard sig')
rep("""<em>${n} class${n === 1 ? '' : 'es'}</em>${pcChev(open ? 90 : 0)}""", """<em>${esc(lab)}</em>${pcChev(open ? 90 : 0)}""", 'agCard label')

# Plans: every plan shows them
rep("""    const days = DAYS.map(d => [d, timed.filter(s => s.days.includes(d)).sort((a, b) => a.s - b.s)]).filter(x => x[1].length);
    inner = `<div class="pad" style="margin-top:14px"><div class="seg plans">""", """    const days = DAYS.map(d => [d, timed.filter(s => s.days.includes(d)).sort((a, b) => a.s - b.s)]).filter(x => x[1].length || cmDayWords(x[0]));
    inner = `<div class="pad" style="margin-top:14px"><div class="seg plans">""", 'plan days')
rep("""timed.length ? grid(timed, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330, faces: true }) : '<div class="empty"><b>No timed classes</b>Add classes from Explore.</div>'}</div>""",
    """timed.length || TC.commits.length ? grid(timed, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330, faces: true, extra: cmBlocks('me') }) + cmWeekend() : '<div class="empty"><b>No timed classes</b>Add classes from Explore.</div>'}</div>""", 'plan grid')
rep("""agCard('plan' + S.plan, d, list.length, d === CLOCK.day, '', () => list.map(s => {""", """agCard('plan' + S.plan, d, list.length, d === CLOCK.day, '', () => cmMix(list, d, s => {""", 'plan rows')
S_i = S.index("""agCard('plan' + S.plan, d, list.length, d === CLOCK.day, '', () => cmMix(list, d, s => {""")
j = S.index("""}).join(''))).join('')}""", S_i)
S = S[:j] + """}).join(''), cmDayWords(d))).join('')}""" + S[j + len("""}).join(''))).join('')}"""):]

# Home: your week and friends' (their Busy)
rep("""grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300 })""",
    """grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300, extra: /^[ABC]$/.test(v.k) ? [] : cmBlocks(isMe ? 'me' : id) })""", 'home grid')
# a friend's page: their Busy on the week they're in
rep("""body = secs.length ? grid(secs, { sel: S.homeDays['f:' + id + (k === 'next' ? ':n' : '')], act: 'homeDay', key: 'f:' + id + (k === 'next' ? ':n' : ''), blockAct: 'secSheet', shared, one: true, H: 280 })""",
    """body = secs.length ? grid(secs, { sel: S.homeDays['f:' + id + (k === 'next' ? ':n' : '')], act: 'homeDay', key: 'f:' + id + (k === 'next' ? ':n' : ''), blockAct: 'secSheet', shared, one: true, H: 280, extra: k === 'now' ? cmBlocks(id) : [] })""", 'friend grid')

# ---------- the Builder: asked first; never drafts over them
rep("""  const data = !none || !!TC.audit || fy;
  if (data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);""",
    """  const data = !none || !!TC.audit || fy;
  /* (2026-10-11) asked about work and practice before Plans A, B and C first draft; plans that exist stay */
  const asked = cmAsked(), waiting = !asked && !AT_PLANS.some(x => (TC.plans[x] || []).length);
  if (asked && data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);""", 'builder gate')
rep("""  ${planCard(k, L, R, data ? '' : 'nodata')}""", """  ${asked ? '' : cmAskCard()}
  ${waiting ? cmWaitCard(k) : planCard(k, L, R, data ? '' : 'nodata')}""", 'builder card')
rep("""<div class="pl-recs">${esc(sum)}</div>""", """<div class="pl-recs">${esc(sum)}</div>${TC.commits.length ? `<button class="pl-clear" data-a="sheet" data-x="cmList"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"></path></svg>Clear of your ${esc(cmWords())}</button>` : ''}""", 'clear line')
rep("""function plDraftSec(code, have, used) {
  const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id] && !(have || []).some(t => secClash(s, t)));""",
    """function plDraftSec(code, have, used) {
  /* (2026-10-11) never over your work, practice and the rest */
  const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id] && !(have || []).some(t => secClash(s, t)) && !TC.commits.some(t => secClash(s, t)));""", 'draft clear')

# ---------- the sheets
rep("""function regReadTime(sh) {""", r"""/* Add work / practice / a club / something else, or edit one (the kind is the title; never asked again) */
const cmT = m => m == null ? '' : String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');
const cmM = t => { const v = String(t || ''); return /^([01]\d|2[0-3]):[0-5]\d$/.test(v.slice(0, 5)) ? +v.slice(0, 2) * 60 + +v.slice(3, 5) : null; };
SHEETS.cm = sh => {
  const busy = !!UI.busy.cm, title = sh.id ? 'Edit ' + (cmLabel(sh) || 'this') : CM_ADD[sh.kind] || CM_ADD.other;
  const day = (d, l) => `<button class="cm-d${sh.days.includes(d) ? ' on' : ''}" data-a="cmDay" data-x="${d}" aria-pressed="${sh.days.includes(d)}" aria-label="${DAYL[d]}">${l}</button>`;
  return `<div class="row sb"><h3>${esc(title)}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <label class="cm-l" for="cm-name">Name (only you see it)</label><input id="cm-name" class="cm-f" maxlength="40" value="${esc(sh.name || '')}" placeholder="${esc(CM_KINDS[sh.kind] || 'What is it?')}" autocomplete="off">
  <span class="cm-l">Which days</span><div class="cm-days" role="group" aria-label="Which days">${day('M', 'M')}${day('T', 'T')}${day('W', 'W')}${day('R', 'Th')}${day('F', 'F')}${day('S', 'Sa')}${day('U', 'Su')}</div>
  <div class="cm-two"><span><label class="cm-l" for="cm-from">From</label><input id="cm-from" class="cm-f" type="time" step="300" value="${esc(sh.from || '')}"></span><span><label class="cm-l" for="cm-to">To</label><input id="cm-to" class="cm-f" type="time" step="300" value="${esc(sh.to || '')}"></span></div>
  <div class="rd-row"><span class="grow"><span class="b" style="display:block;font-size:15px">Friends see you’re busy</span><span class="muted b" style="display:block;font-size:12.5px">They see “Busy” on your week, never what it is</span></span><button class="toggle ${sh.busy ? 'on' : 'off'}" data-a="cmBusy" role="switch" aria-checked="${!!sh.busy}" aria-label="Friends see you’re busy"><i></i></button></div>
  ${sh.err ? `<div class="tc-err">${esc(sh.err)}</div>` : ''}
  <button class="btn" style="margin-top:14px" data-a="cmSave" ${busy ? 'disabled' : ''}>${busy ? 'Saving…' : 'Save'}</button>
  ${sh.id ? `<button class="btn soft" style="margin-top:8px" data-a="cmDrop" ${busy ? 'disabled' : ''}>Remove</button>` : ''}`;
};
/* what the Builder keeps clear: each one (tap to edit) and Add */
SHEETS.cmList = () => `<div class="row sb"><h3>Your week outside class</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <div class="muted b" style="font-size:13.5px;margin:2px 0 8px;line-height:1.4">On My Classes and Plans A, B and C. The Builder won’t put a class over these.</div>
  ${TC.commits.map(x => `<button class="cm-li" data-a="cmOpen" data-x="${esc(x.id)}"><span class="cm-sw" aria-hidden="true"></span><span class="grow"><b>${esc(cmLabel(x))}</b><span>${esc(cmDaysText(x.days))} · ${hs(x.s)}–${hs(x.e)}</span></span><em>${x.busy ? 'Friends see Busy' : 'Only you'}</em></button>`).join('')}
  <div class="cm-picks" style="margin-top:12px">${['work', 'practice', 'club'].map(k => `<button class="cm-pick" data-a="cmAdd" data-x="${k}">${CM_KINDS[k]}</button>`).join('')}<button class="cm-pick wide" data-a="cmAdd" data-x="other">Something else</button></div>`;
function cmRead(sh) { const g = id => document.getElementById(id); if (g('cm-name')) sh.name = String(g('cm-name').value || '').slice(0, 40); if (g('cm-from')) sh.from = String(g('cm-from').value || '').slice(0, 5); if (g('cm-to')) sh.to = String(g('cm-to').value || '').slice(0, 5); }
/* what's typed is kept as it's typed, so nothing that redraws the sheet loses it */
['input', 'change'].forEach(ev => document.addEventListener(ev, e => { const t = e.target; if (t && /^cm-(name|from|to)$/.test(t.id || '') && UI.sheet && UI.sheet.type === 'cm') cmRead(UI.sheet); }, true));
function regReadTime(sh) {""", 'sheets')
rep("""  pcProfNone: () =>""", """  cmAdd: k => { UI.sheet = { type: 'cm', kind: k in CM_KINDS ? k : 'other', name: CM_KINDS[k] || '', days: '', from: '', to: '', busy: true, ret: UI.sheet && UI.sheet.type === 'cmList' ? { type: 'cmList' } : null }; render(true); },
  cmOpen: id => { const x = TC.commits.find(c => c.id === id); if (!x) return; UI.sheet = { type: 'cm', id: x.id, kind: x.kind, name: x.name, days: x.days, from: cmT(x.s), to: cmT(x.e), busy: x.busy }; render(true); },
  cmDay: d => { const sh = UI.sheet; if (!sh || sh.type !== 'cm') return; cmRead(sh); sh.days = sh.days.includes(d) ? sh.days.replace(d, '') : 'MTWRFSU'.split('').filter(x => x === d || sh.days.includes(x)).join(''); sh.err = null; render(true); },
  cmBusy: () => { const sh = UI.sheet; if (!sh || sh.type !== 'cm') return; cmRead(sh); sh.busy = !sh.busy; render(true); },
  cmSkip: () => { cmAskedSet(); render(true); },
  cmSave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'cm' || UI.busy.cm) return; cmRead(sh);
    const s = cmM(sh.from), e = cmM(sh.to);
    sh.err = !sh.days ? 'Pick at least one day.' : s == null || e == null ? 'Add when it starts and ends.' : e <= s ? 'It has to end after it starts.' : null;
    if (sh.err) { render(true); return; }
    const x = { id: sh.id || cmId(), kind: sh.kind, name: String(sh.name || '').trim().slice(0, 40), days: sh.days, s, e, busy: !!sh.busy }, isNew = !sh.id;
    UI.busy.cm = 1; render(true);
    let err; try { err = await TC.saveCommit(x); } finally { UI.busy.cm = 0; }
    UI.sheet = null; UI.plRefresh = true; render(true);
    toast(err || (isNew ? `${cmLabel(x)} added to My Classes and Plans A, B and C` : 'Saved'));
  },
  cmDrop: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'cm' || !sh.id || UI.busy.cm) return;
    UI.busy.cm = 1; render(true);
    let err; try { err = await TC.dropCommit(sh.id); } finally { UI.busy.cm = 0; }
    UI.sheet = null; UI.plRefresh = true; render(true); toast(err || 'Removed');
  },
  pcProfNone: () =>""", 'actions')
rep(""".pl-why{display:flex""", """.cm-ask{padding:18px 16px 12px}.cm-askh{display:flex;gap:12px;align-items:flex-start}.cm-askh b{display:block;font-size:19px;font-weight:900;line-height:1.2}.cm-askh span>span{display:block;font-size:14.5px;font-weight:700;color:var(--ink3);line-height:1.45;margin-top:6px}
.cm-ico{width:44px;height:44px;border-radius:14px;background:var(--blue-soft);display:grid;place-items:center;flex:none}
.cm-picks{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:16px}
.cm-pick{display:flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 8px;border-radius:14px;background:var(--fill);border:1px solid var(--line2);color:var(--ink);font:inherit;font-size:15px;font-weight:900;cursor:pointer}.cm-pick.wide{grid-column:1/-1}
.cm-skip{width:100%;margin-top:10px;border:0;background:none;color:var(--blue-t,var(--blue));font:inherit;font-size:15px;font-weight:900;min-height:44px;cursor:pointer}
.cm-wait{opacity:.5}
.pl-clear{display:flex;align-items:center;gap:8px;width:100%;margin:8px 0 6px;padding:9px 10px;min-height:44px;border:0;border-radius:12px;background:var(--blue-soft);color:var(--blue-ink);font:inherit;font-size:13px;font-weight:800;text-align:left;cursor:pointer}
.cm-l{display:block;font-size:12px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:16px 0 8px}
.cm-f{display:block;width:100%;box-sizing:border-box;height:50px;border-radius:14px;border:1px solid var(--line2);background:var(--bg);color:var(--ink);font:inherit;font-size:16px;font-weight:800;padding:0 14px}
.cm-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px}
.cm-d{height:44px;border-radius:12px;border:1px solid var(--line2);background:var(--fill);color:var(--ink3);font:inherit;font-size:14px;font-weight:900;cursor:pointer}.cm-d.on{background:var(--blue);border-color:var(--blue);color:#fff}
.cm-two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.cm-li{display:flex;align-items:center;gap:12px;width:100%;min-height:56px;padding:8px 0;border:0;border-top:1px solid var(--line);background:none;color:var(--ink);font:inherit;text-align:left;cursor:pointer}
.cm-li b{display:block;font-size:15px;font-weight:900}.cm-li .grow>span{display:block;font-size:13px;font-weight:800;color:var(--muted)}.cm-li em{font-style:normal;font-size:12px;font-weight:800;color:var(--muted)}
.cm-sw{width:24px;height:24px;border-radius:7px;flex:none;background:repeating-linear-gradient(135deg,var(--fill2) 0 4px,var(--fill) 4px 8px);border:1px solid var(--line2)}
.g-cm{position:absolute;left:3px;right:3px;border-radius:8px;background:repeating-linear-gradient(135deg,var(--fill2) 0 5px,var(--fill) 5px 10px);border:1px solid var(--line2);color:var(--ink3);font:inherit;font-size:10px;font-weight:900;padding:0;display:grid;place-items:center;overflow:hidden;box-sizing:border-box;cursor:pointer}
.g-cm>span{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;max-width:100%;padding:0 2px;line-height:1.12;text-align:center;overflow:hidden;overflow-wrap:anywhere}.g-cm.fr{cursor:default}
.cm-vb{background:repeating-linear-gradient(180deg,var(--muted) 0 4px,transparent 4px 7px)!important}
.cm-wkend{display:flex;align-items:center;gap:8px;margin:10px 14px 0 44px;font-size:12.5px;font-weight:800;color:var(--ink4)}.cm-wkend .cm-sw{width:14px;height:14px;border-radius:4px}
.pl-why{display:flex""", 'css')
open(PA, 'w', encoding='utf-8').write(S); print('commitments: done')
