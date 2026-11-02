#!/usr/bin/env python3
"""Tate, 2026-10-31: the contacts designs he picked from mock/contacts.html (1a, 1b, list A).
  1a  sign-up phone step, stronger: "What's your number?", a phone tile, a +1 field, a big Continue and a
      small grey "Not now" (still skippable: Apple 5.1.1).
  1b  students who already signed up and have no number saved (TC.phoneSaved === false, never null/true):
      one small "Add your number · So friends can find you" pop-up, through the pop-up queue (the day's one
      pop-up), on Home only, after "Connect contacts" has had its turn and before notifications, at most twice
      in all, 7+ days apart (and 7+ days after a "Not now" at sign-up).
  A   the synced contacts list: a full page "Contacts" + close, a search box (both sections), "On TermChamp"
      (photo/initials, @handle · major or N mutual, blue Add / Requested / Friends), then "Invite to TermChamp"
      A to Z with sticky letters, an outlined Invite and the number under the name. Named contacts first
      (locale-aware, case and accents ignored), number-only contacts last under "Other numbers" (the bug Tate
      saw: bare numbers were sorting first). An A-Z scrubber on the right (tap or drag). A number saved twice
      is listed once, under its name. Fast with 1,000+ contacts: groups are content-visibility:auto, the
      invite list's HTML is cached, and typing in search repaints only the list.
The Friends header is unchanged. Run after contacts-2026-10-30, contacts-into-popqueue and popup-limits."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
def span(a, z, b):
    """replace from the unique `a` up to (not including) the unique `z` that follows it"""
    global s
    assert s.count(a) == 1, (a[:70], s.count(a)); i = s.index(a)
    assert s.count(z) == 1, (z[:70], s.count(z)); j = s.index(z); assert j > i, (a[:40], z[:40])
    s = s[:i] + b + s[j:]

# ---------------------------------------------------------------- CSS
one(""".ct-set .pbtn{flex:none}""", r""".ct-set .pbtn{flex:none}
/* (2026-10-31) contacts list A: a full page on the app background (the status bar is that colour too); the top (title + search) sticks, letters stick under it */
.ctp{min-height:100%;background:var(--bg);padding:0 16px calc(env(safe-area-inset-bottom,0px) + 28px);color:var(--ink)}
.ctp-top{position:sticky;top:0;z-index:3;background:var(--bg);margin:0 -16px;padding:calc(var(--sb) + 6px) 16px 10px;height:calc(var(--sb) + 108px)}
.ctp-hd{display:flex;align-items:center;justify-content:space-between;height:44px;margin-bottom:8px}
.ctp-t{font-size:28px;font-weight:900;letter-spacing:-.01em;margin:0}
.ctp .xbtn{background:var(--card);box-shadow:inset 0 0 0 1px var(--line)}
.ctp-q{display:flex;align-items:center;gap:8px;height:40px;border-radius:12px;background:var(--card);box-shadow:inset 0 0 0 1px var(--line);padding:0 12px;color:var(--muted)}
.ctp-q:focus-within{box-shadow:0 0 0 2px var(--blue)}
.ctp-q input{flex:1;min-width:0;height:100%;font-size:16px;font-weight:700;color:var(--ink);-webkit-appearance:none;appearance:none}
.ctp-q input::placeholder{color:var(--muted)}
.ctp-q input::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none}
.ct-idx{position:absolute;right:0;top:calc(100% + 6px);width:24px;display:flex;flex-direction:column;align-items:center;touch-action:none;user-select:none;-webkit-user-select:none;padding:4px 0}
.ct-idx button{width:24px;height:15px;font-size:10.5px;font-weight:900;line-height:15px;text-align:center;color:var(--blue-t,var(--blue))}
.ct-idx button.off{color:var(--muted2);opacity:.55}
.ctp.q .ct-idx{display:none}
.ctp.idx #ctBody{padding-right:14px}
.ct-sec{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:900;margin:14px 0 4px;min-height:32px}
.ct-sec .grow{flex:1}
.ct-n{display:inline-grid;place-items:center;min-width:22px;height:20px;padding:0 7px;border-radius:999px;background:var(--green-wash);color:var(--green-ink3);font-size:12px;font-weight:900}
.ct-addall{color:var(--blue-t,var(--blue));font-weight:900;font-size:14px;min-height:36px;padding:0 4px}
.ctp .ct-row{display:flex;align-items:center;gap:12px;height:60px;padding:0;border-top:0}
.ctp .ct-row .nm{font-size:15.5px;font-weight:900;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ctp .ct-row .sub{font-size:13px;font-weight:700;color:var(--ink4);line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ctp .ct-row .grow{flex:1;min-width:0}
.ct-av{width:42px;height:42px;border-radius:50%;display:grid;place-items:center;font-weight:900;font-size:14px;color:#0F172A;flex:none;overflow:hidden}
.ct-av .av{border-radius:50%}
.ct-av.iv{background:var(--fill2);color:var(--ink4)}
.ctp .pbtn{height:32px;padding:0 15px;border-radius:999px;font-size:13.5px}
.ctp .pbtn.done{background:none;color:var(--ink4);box-shadow:inset 0 0 0 1.5px var(--line2)}
.ctp .pbtn.ct-inv{background:none;color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--line2)}
.ctp .pbtn.ct-inv.done{color:var(--ink4);font-weight:800}
.ct-grp{content-visibility:auto}
.ct-lh{position:sticky;top:calc(var(--sb) + 108px);z-index:1;height:28px;display:flex;align-items:center;background:var(--bg);font-size:12.5px;font-weight:900;letter-spacing:.06em;color:var(--ink4);border-bottom:1px solid var(--line)}
.ctp .ct-mine{margin:8px 0 2px}
.ctp .ct-none{font-size:14px;font-weight:700;color:var(--ink4);padding:4px 0 8px;line-height:1.45}
/* (2026-10-31) 1b: the small "Add your number" pop-up */
.ctpp-hd{display:flex;align-items:center;gap:12px}
.ctpp-hd .grow{flex:1;min-width:0}
.ctpp-hd h3{margin:0;font-size:19px;line-height:1.2}
.ctpp-ic{width:44px;height:44px;border-radius:14px;background:var(--blue-soft);color:var(--blue-t,var(--blue));display:grid;place-items:center;flex:none}
.ctpp .ct-tel{margin:16px 0 4px}
.ctpp .btn.ghost.ctpp-no{color:var(--muted);height:44px;font-size:15px}""")

# 1a's CSS goes with the onboarding styles (unlayered, so it outranks the app layer)
one(""".onb .onb-ico.teal{background:#0F766E}""", """.onb .onb-ico.teal{background:#0F766E}
/* (2026-10-31) 1a: the sign-up step */
.onb .onb-ico.ct-ph{width:64px;height:64px;border-radius:20px;background:var(--blue-soft);color:var(--blue)}
.onb .unwrap.cc2 .at{gap:6px;top:14px;height:24px;padding-right:10px;border-right:1.5px solid var(--track)}
.onb .unwrap.cc2 .at .fl{font-size:17px;line-height:1}
.onb .unwrap.cc2 .input{padding-left:86px}
.onb .foot .ghost.ct-later{font-size:14px;min-height:40px}""")

# ---------------------------------------------------------------- reading the book: named cards first, so a
# number saved twice (named and bare) is listed once, under the name
one("""  const people = [], phoneH = [], mailH = [], byHash = {}, seenPhone = new Set();
  for (const c of list) {""", """  const people = [], phoneH = [], mailH = [], byHash = {}, seenPhone = new Set();
  /* (2026-10-31) named cards first: a number saved twice (with a name and without) is listed once, under the name */
  const named = list.filter(c => ctName(c)), bare = list.filter(c => !ctName(c));
  for (const c of named.concat(bare)) {""")
one("""    const name = ctName(c) || (phones[0] ? ctShowPhone(phones[0]) : mails[0]);
    const k = people.length; people.push({ k, name, phone: phones.find(x => !seenPhone.has(x)) || '', hit: false });""",
    """    const nm = ctName(c), name = nm || (phones[0] ? ctShowPhone(phones[0]) : mails[0]);
    const k = people.length; people.push({ k, name, named: !!nm, phone: phones.find(x => !seenPhone.has(x)) || '', hit: false });""")
one("""    st.invite = book.people.filter(x => !x.hit && x.phone).sort((a, b) => a.name.localeCompare(b.name));""",
    """    st.invite = ctSortBook(book.people.filter(x => !x.hit && x.phone));   /* (2026-10-31) A to Z, bare numbers last */""")
one("""  const st = UI.ct = { busy: 1, rows: [], invite: [], err: '', unavail: false, limited: false, all: (UI.ct && UI.ct.all) || false, invited: (UI.ct && UI.ct.invited) || {} };""",
    """  const st = UI.ct = { busy: 1, rows: [], invite: [], err: '', unavail: false, limited: false, all: (UI.ct && UI.ct.all) || false, invited: (UI.ct && UI.ct.invited) || {}, q: '' };""")

# ---------------------------------------------------------------- list A
span("""SHEETS.ctResults = () => {""", """/* Your own number: the sign-up step and this sheet""", r"""/* ---- The contacts list (2026-10-31, Tate's pick "A") ----
   A full page. Named contacts A to Z (Intl.Collator: case and accents ignored, numbers in order), then names
   that don't start with a letter under "#", then number-only contacts under "Other numbers". */
const CT_ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#~', CT_IDX_MIN = 15;
let CT_COLL = null;
function ctColl() { if (!CT_COLL) { try { CT_COLL = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true }); } catch (e) { CT_COLL = { compare: (a, b) => a.localeCompare(b) }; } } return CT_COLL; }
function ctFold(t) { return String(t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
function ctLetter(name) { const c = ctFold(name).replace(/^[^\p{L}\p{N}]+/u, '').charAt(0).toUpperCase(); return /^[A-Z]$/.test(c) ? c : '#'; }
function ctSortBook(list) {
  const co = ctColl();
  list.forEach(x => { x.L = x.named ? ctLetter(x.name) : '~'; x.f = ctFold(x.name); x.d = String(x.phone || '').replace(/\D/g, ''); x.s = x.name.replace(/^[^\p{L}\p{N}]+/u, ''); });   /* "Coach" Reed sorts as Coach */
  return list.sort((a, b) => CT_ABC.indexOf(a.L) - CT_ABC.indexOf(b.L) || (a.named ? co.compare(a.s, b.s) : a.d.localeCompare(b.d)) || a.k - b.k);
}
/* search: every word in the name (case and accents ignored), or 3+ digits anywhere in the number */
function ctMatcher(q) {
  const w = ctFold(q).trim().split(/\s+/).filter(Boolean), dg = String(q || '').replace(/\D/g, '');
  if (!w.length) return null;
  return (txt, digits) => w.every(x => txt.includes(x)) || (dg.length >= 3 && !!digits && digits.includes(dg));
}
function ctMutual(id) { let n = 0; (TC.friends || []).forEach(f => { const o = TC.fof && TC.fof[f]; if (o && o.ids && o.ids.includes(id)) n++; }); return n; }
function ctOnBtn(id) {
  const rel = TC.relation(id), nm = esc(PEOPLE[id].name);
  return rel === 'friends' ? '<span class="pbtn done">Friends</span>' : rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${esc(id)}">Accept</button>`
    : rel === 'sent' ? `<button class="pbtn done" data-a="addFriend" data-x="${esc(id)}" aria-label="Cancel friend request to ${nm}">Requested</button>` : `<button class="pbtn" data-a="addFriend" data-x="${esc(id)}" aria-label="Add ${nm}">Add</button>`;
}
function ctOnRow(id) {
  const p = PEOPLE[id], img = safeImg(p.avatar), mu = p.major ? '' : ctMutual(id);
  const av = img ? `<span class="ct-av">${pav(id, 42, 14)}</span>` : `<span class="ct-av" style="background:${p.color || colorFor(id)}" aria-hidden="true">${esc(p.ini || initialsOf(p.name))}</span>`;
  const sub = [p.handle ? '@' + esc(p.handle) : '', p.major ? esc(p.major) : mu ? mu + ' mutual' : ''].filter(Boolean).join(' · ');
  return `<div class="ct-row">${av}<div class="grow"><div class="nm">${esc(p.name)}</div>${sub ? `<div class="sub">${sub}</div>` : ''}</div>${ctOnBtn(id)}</div>`;
}
function ctIvRow(c, done) {
  const ini = c.named ? esc(initialsOf(c.name)) : ic('phone', 18, 2.3);
  return `<div class="ct-row"><span class="ct-av iv" aria-hidden="true">${ini}</span><div class="grow"><div class="nm">${esc(c.name)}</div>${c.named ? `<div class="sub">${esc(ctShowPhone(c.phone))}</div>` : ''}</div><button class="pbtn ct-inv${done ? ' done' : ''}" data-a="ctInvite" data-x="${c.k}" aria-label="Invite ${esc(c.name)}">${done ? 'Invited' : 'Invite'}</button></div>`;
}
/* the invite groups, built once per search / invite (1,000+ rows stay cheap on every other render) */
function ctInviteHTML(st, m) {
  const inv = st.invited || {}, key = (st.q || '') + '|' + Object.keys(inv).length + '|' + st.invite.length;
  if (st._ivKey === key && st._iv) return st._iv;
  const list = m ? st.invite.filter(c => m(c.f, c.d)) : st.invite, groups = [];
  let g = null;
  for (const c of list) { if (!g || g.L !== c.L) groups.push(g = { L: c.L, rows: [] }); g.rows.push(c); }
  const html = groups.map(x => `<div class="ct-grp" data-l="${x.L}" style="contain-intrinsic-size:auto ${28 + x.rows.length * 60}px"><div class="ct-lh" role="heading" aria-level="3">${x.L === '~' ? 'Other numbers' : x.L}</div>${x.rows.map(c => ctIvRow(c, inv[c.phone])).join('')}</div>`).join('');
  st._ivKey = key; st._iv = html; st._ivN = list.length;
  return html;
}
function ctBodyHTML(st) {
  if (st.busy) return loadingCard('Checking your contacts…');
  const m = ctMatcher(st.q), ivH = st.invite.length ? ctInviteHTML(st, m) : '', ivN = st.invite.length ? st._ivN : 0;
  const inv = ivN ? `<div class="ct-sec">Invite to TermChamp</div>${ivH}` : '';
  if (st.err) return `<div class="tc-err" role="alert">${esc(st.err)}</div><button class="btn soft" style="margin-top:8px" data-a="ctRetry">Try again</button>` + inv;
  const rows = m ? (st.rows || []).filter(id => { const p = PEOPLE[id]; return m(ctFold(p.name + ' ' + (p.handle || '')), ''); }) : (st.rows || []);
  const addable = rows.filter(id => TC.relation(id) === '').length;
  const on = st.unavail ? (m ? '' : '<div class="ct-note" role="status">Contact matching isn’t available yet.</div>')
    : rows.length ? `<div class="ct-sec"><span>On TermChamp</span><span class="ct-n">${rows.length}</span><span class="grow"></span>${addable > 1 && !m ? `<button class="ct-addall" data-a="ctAddAll" ${UI.busy.ctAll ? 'disabled' : ''}>${UI.busy.ctAll ? 'Adding…' : 'Add all'}</button>` : ''}</div>${rows.map(ctOnRow).join('')}`
    : m ? '' : '<div class="ct-sec">On TermChamp</div><div class="ct-none">None of your contacts are on TermChamp yet. Invite a few below.</div>';
  const mine = !m && TC.phoneSaved === false && !st.unavail ? `<button class="ct-mine" data-a="ctPhoneSheet" data-x="ctResults">${ic('phone', 18, 2.3)}<span class="grow">Add your number so friends can find you too</span>${ic('chevR', 16, 2.6)}</button>` : '';
  const lim = !m && st.limited ? '<div class="muted b" style="font-size:12.5px;line-height:1.4;margin-top:8px">You shared some of your contacts. Change which in your iPhone’s Settings › TermChamp › Contacts.</div>' : '';
  const none = m && !rows.length && !ivN ? `<div class="ct-none" role="status" style="padding-top:14px">No contacts match “${esc(String(st.q).trim())}”.</div>` : '';
  return on + mine + lim + inv + none;
}
function ctIdxHTML(st) {
  if (st.busy || st.invite.length < CT_IDX_MIN) return '';
  const has = new Set(st.invite.map(c => c.L === '~' ? '#' : c.L));   /* letters come from the whole list */
  return `<div class="ct-idx" aria-hidden="true">${CT_ABC.slice(0, 27).split('').map(L => `<button type="button" tabindex="-1" class="${has.has(L) ? '' : 'off'}" data-a="ctJump" data-x="${L}">${L}</button>`).join('')}</div>`;
}
SHEETS.ctResults = () => {
  const st = UI.ct || { busy: 1, rows: [], invite: [] }, idx = ctIdxHTML(st), q = String(st.q || '');
  return `<div class="ctp${idx ? ' idx' : ''}${q.trim() ? ' q' : ''}"><div class="ctp-top"><div class="ctp-hd"><h2 class="ctp-t">Contacts</h2><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <label class="ctp-q">${ic('search', 17, 2.5)}<input id="ctQ" data-in="ctQ" type="search" enterkeyhint="search" autocomplete="off" autocorrect="off" spellcheck="false" placeholder="Search contacts" aria-label="Search contacts" value="${esc(q)}" ${st.busy ? 'disabled' : ''}></label>${idx}</div>
 <div id="ctBody" class="ct">${ctBodyHTML(st)}</div></div>`;
};
SHEETS.ctResults.full = true; SHEETS.ctResults.label = 'Contacts';
/* typing repaints only the list, so the field (and the iPhone keyboard) stays put */
document.addEventListener('input', ev => {
  const t = ev.target; if (!t || !t.dataset || t.dataset.in !== 'ctQ' || !UI.ct) return;
  UI.ct.q = t.value;
  const b = document.getElementById('ctBody'), pg = document.querySelector('#sheet .ctp'); if (!b || !pg) return render(true);
  b.innerHTML = ctBodyHTML(UI.ct); pg.classList.toggle('q', !!t.value.trim());
  const fp = pg.closest('.fullpg'); if (fp) fp.scrollTop = 0;
});
/* the A-Z scrubber: tap a letter, or drag along it (a letter with nobody goes to the next one that has someone) */
function ctJump(L) {
  const fp = document.querySelector('#sheet .fullpg'), top = fp && fp.querySelector('.ctp-top'); if (!top) return false;
  const want = CT_ABC.indexOf(L), g = [...fp.querySelectorAll('.ct-grp[data-l]')].find(x => CT_ABC.indexOf(x.dataset.l) >= want); if (!g) return false;
  fp.scrollTop += g.getBoundingClientRect().top - top.getBoundingClientRect().bottom;
  return g.dataset.l;
}
const CTX = { el: null, last: '' };
function ctIdxAt(el, y) {
  const r = el.getBoundingClientRect(), hit = document.elementFromPoint(r.left + r.width / 2, y), b = hit && hit.closest && hit.closest('.ct-idx button');
  if (b && el.contains(b)) return b.dataset.x;
  const bs = el.querySelectorAll('button'); return y < r.top + r.height / 2 ? (bs[0] || {}).dataset.x : (bs[bs.length - 1] || {}).dataset.x;   /* past either end */
}
/* the finger goes down: jump there, then follow it (captured, so the drag doesn't scroll the list) */
document.addEventListener('pointerdown', ev => { const el = ev.target && ev.target.closest && ev.target.closest('.ct-idx'); if (!el) return; CTX.el = el; CTX.last = ctIdxAt(el, ev.clientY); if (CTX.last) ctJump(CTX.last); try { el.setPointerCapture(ev.pointerId); } catch (e) {} });
document.addEventListener('pointermove', ev => { if (!CTX.el) return; const L = ctIdxAt(CTX.el, ev.clientY); if (L && L !== CTX.last) { CTX.last = L; ctJump(L); } });
['pointerup', 'pointercancel'].forEach(t => document.addEventListener(t, () => { CTX.el = null; }));
""")

# ---------------------------------------------------------------- 1a: the sign-up step
span("""function onbPhone() {""", """document.addEventListener('input', ev => { if (ev.target && ev.target.dataset && ev.target.dataset.in === 'ctPhone') UI.ctPhoneVal = ev.target.value; });""",
r"""function onbPhone() {
  /* (2026-10-31) stronger (Tate's 1a): the question as the title, a big Continue, a quiet "Not now" — still skippable (Apple 5.1.1) */
  const saved = TC.phoneSaved === true;
  return `<form class="scr" data-submit="ctPhoneOnb" novalidate>${onbTop({ progress: 2 })}<div class="body">
    <div class="stack"><div class="onb-ico ct-ph">${ic('phone', 30, 2.2)}</div><h1>What’s your number?</h1><p class="lead">Friends who have you saved will find you on TermChamp. It’s never shown on your profile.</p></div>
    ${saved ? `<div class="banner" role="status">${ONB_I.check}Your number is saved</div>` : `<div class="field"><div class="unwrap cc cc2"><span class="at" aria-hidden="true"><span class="fl">🇺🇸</span>+1</span><input class="input" id="ob-phone" data-in="ctPhone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(805) 555-0134" aria-label="Phone number" maxlength="20" value="${esc(UI.ctPhoneVal || '')}"></div>
    <div class="hint bad" role="alert" id="ob-phoneerr">${esc(UI.ctPhoneErr || '')}</div></div>`}</div>
    <div class="foot"><button class="btn" type="submit" ${UI.busy.ctPhone ? 'disabled' : ''}>${UI.busy.ctPhone ? 'Saving…' : 'Continue'}</button>
    <button type="button" class="ghost ct-later" data-a="ctPhoneSkip">Not now</button></div></form>`;
}
""")
# Continue with nothing typed is a "Not now" too (it counts for the 1b pop-up's 7 days)
one("""  if (TC.phoneSaved === true || !String(v).trim()) { UI.ctPhoneErr = ''; return onbGo('people'); }""",
    """  if (TC.phoneSaved === true || !String(v).trim()) { UI.ctPhoneErr = ''; if (TC.phoneSaved !== true) ctSet({ phSkip: Date.now() }); return onbGo('people'); }""")
one("""  ctPhoneSkip: () => { UI.ctPhoneErr = ''; UI.ctPhoneVal = ''; onbGo('people'); },""",
    """  ctPhoneSkip: () => { UI.ctPhoneErr = ''; UI.ctPhoneVal = ''; ctSet({ phSkip: Date.now() }); onbGo('people'); },""")

# ---------------------------------------------------------------- 1b: the pop-up for students already signed up
one("""/* Settings › Contacts */
function ctSettings() {""", r"""/* ---- "Add your number" (2026-10-31, Tate's 1b) ----
   For students already signed up with no number saved (TC.phoneSaved === false; never when the server
   can't say: null = the SQL isn't there, undefined = the read failed). It waits its turn in the pop-up queue,
   right after "Connect contacts" (on the iPhone it shows only once contacts is connected or has been asked)
   and before notifications: on an app open, on Home, the day's one pop-up, twice in all, 7+ days apart
   (and 7+ days after a "Not now" at sign-up). Settings › Contacts always has it too. */
const CT_PH_MAX = 2, CT_PH_GAP = 7 * 864e5;
POPS.splice(POPS.findIndex(k => k.kind === 'contacts') + 1, 0, { kind: 'phone',
  due: async at => {
    if (at !== 'open' || !TC.user || TC.phase !== 'ok' || UI.sheetNext || !popLaterOpen()) return null;
    const st = ctState(), e = cur();
    if (S.tab !== 'home' || !e || e.s !== 'home' || st.phOk || (+st.pk || 0) >= CT_PH_MAX) return null;
    if (Date.now() - Math.max(+st.pat || 0, +st.phSkip || 0) < CT_PH_GAP) return null;
    if (ctAvail() && !st.on && !(+st.k || 0)) return null;   /* "Connect contacts" goes first */
    if (TC.phoneSaved === undefined) await ctPhoneLoad();
    if (TC.phoneSaved === true) ctSet({ phOk: 1 });   /* saved (maybe on another phone): never asks again here */
    return TC.phoneSaved === false ? 'later' : null;
  },
  show: () => ctPhonePop() });
function ctPhonePop() {
  if (!TC.user || TC.phase !== 'ok' || UI.sheet || UI.champ || TC.phoneSaved !== false) return false;
  const st = ctState(); ctSet({ pk: (+st.pk || 0) + 1, pat: Date.now() }); popMarkDay();   /* closing it any way counts as "Not now" */
  UI.ctPhoneErr = ''; UI.sheet = { type: 'ctPhonePop' }; render(true); return true;
}
SHEETS.ctPhonePop = () => `<form class="ctpp" data-submit="ctPhonePop"><div class="ctpp-hd"><span class="ctpp-ic">${ic('phone', 22, 2.3)}</span><div class="grow"><h3>Add your number</h3><div class="muted b" style="font-size:14px">So friends can find you</div></div><button type="button" class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <label class="ct-tel"><span class="cc" aria-hidden="true">+1</span><input id="ctPopIn" data-in="ctPhone" type="tel" inputmode="tel" autocomplete="tel" placeholder="Phone number" aria-label="Your phone number" value="${esc(UI.ctPhoneVal || '')}" maxlength="20"></label>
 <div class="tc-err" role="alert" style="${UI.ctPhoneErr ? '' : 'display:none'}">${esc(UI.ctPhoneErr || '')}</div>
 <div style="display:grid;gap:4px;margin-top:12px"><button class="btn" ${UI.busy.ctPhone ? 'disabled' : ''}>${UI.busy.ctPhone ? 'Saving…' : 'Save'}</button><button type="button" class="btn ghost ctpp-no" data-a="closeSheet">Not now</button></div></form>`;
SUBMIT.ctPhonePop = async () => {
  if (UI.busy.ctPhone) return;
  const v = (document.getElementById('ctPopIn') || {}).value || UI.ctPhoneVal || '';
  if (!String(v).trim()) { UI.ctPhoneErr = 'Enter your number, or tap Not now.'; return render(true); }
  UI.busy.ctPhone = 1; UI.ctPhoneErr = ''; render(true);
  const r = await ctSaveMine(v); UI.busy.ctPhone = 0;
  if (r.err) { UI.ctPhoneErr = r.err; return render(true); }
  UI.ctPhoneVal = ''; if (UI.sheet && UI.sheet.type === 'ctPhonePop') UI.sheet = null;
  if (r.ok) ctSet({ phOk: 1 });
  toast(r.missing ? 'Saving numbers isn’t switched on yet — add it later in Settings' : 'Number saved. Friends who have it can find you.'); render(true);
};
A.ctJump = L => { ctJump(L); };
/* Settings › Contacts */
function ctSettings() {""")
p.write_text(s); print(p, 'contacts-v2 applied')
