#!/usr/bin/env python3
"""Tate, 2026-10-30: "Connect contacts", like other apps — the mockups he signed off.
  · Friends tab: a blue Contacts pill left of the pink Invite pill (nothing else on the tab changes).
  · Contacts → "Connect contacts" sheet → the iPhone's own permission prompt → "Your contacts":
    On TermChamp · N (Add / Requested / Friends, Add all) and Invite · N (opens Messages with the
    invite text and link; the student sends it). Connected once: Contacts opens the results directly,
    and the contacts are read again each time.
  · The same sheet as a one-time pop-up: after onboarding (after the push ask, never on top of it),
    and once for students who already have an account, on a later app open, on Home, with nothing
    else open. "Not now" (or closing it) = not again for 30 days; connected = never again.
  · Sign-up: an optional "Help friends find you" step right after year/major; Skip is as easy as
    Continue. Skipped: one small row on the results sheet. Settings › Contacts adds/removes it.
Privacy: the address book never leaves the phone. Each number (E.164, +1 for 10 digits) and email
(lower-case) is SHA-256'd on the phone and only the hashes go to match_contacts (1000 a call,
sql/termchamp-contacts-2026-10-30.sql). Names stay on the phone. The student's own number is sent
as one hash to set_my_phone. Before that SQL has run: "Contact matching isn't available yet" and
the Invite list still works. Native: @capacitor-community/contacts 8.0.0 (Capacitor.Plugins.Contacts).
On localhost (the phone preview) a small sample address book stands in so Tate can tap through; on
the real website Connect says "Contacts sync is in the iPhone app".
Works on app/index.html. Not idempotent: run once on a file that has none of it."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
assert 'data-a="ctOpen"' not in s, 'already applied'

# ---- 1. styles -------------------------------------------------------------------------------------
one(""".invpill{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--pink);color:#fff;font-weight:900;font-size:15px;box-shadow:0 4px 12px rgba(219,39,119,.25);flex:none}""",
""".invpill{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--pink);color:#fff;font-weight:900;font-size:15px;box-shadow:0 4px 12px rgba(219,39,119,.25);flex:none}
/* Connect contacts (2026-10-30) */
.fpills{display:flex;gap:8px;flex:none;margin-left:10px}
@media (max-width:380px){.fpills{gap:6px}.fpills .invpill{padding:0 13px;gap:5px}}
.invpill.ctpill{background:var(--blue);box-shadow:0 4px 12px rgba(37,99,235,.25)}
.ct-tile{width:72px;height:72px;border-radius:22px;background:var(--blue-soft);color:var(--blue-t,var(--blue));display:grid;place-items:center;margin:12px auto 14px}
.ct-fine{font-size:12.5px;text-align:center;margin-top:10px;line-height:1.4}
.ct-note{background:var(--bg);color:var(--ink2);border-radius:12px;padding:10px 12px;font-weight:800;font-size:14px;line-height:1.4;margin:8px 0}
.ct-h{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:16px;font-weight:900;margin:16px 0 4px;min-height:36px}
.ct-row{gap:12px;padding:9px 0;border-top:1px solid var(--line)}
.ct-row .nm{font-size:15.5px;line-height:1.25;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ct-row .grow{min-width:0}
.ct-ini{width:44px;height:44px;border-radius:15px;display:grid;place-items:center;font-weight:900;font-size:15px;color:#0F172A;flex:none}
.ct-mine{display:flex;align-items:center;gap:10px;width:100%;min-height:44px;margin:10px 0 2px;padding:8px 12px;border-radius:14px;background:var(--blue-soft);color:var(--blue-t,var(--blue));font-weight:800;font-size:14px;text-align:left}
.ct-mine .grow{flex:1}
.ct-all{display:block;width:100%;min-height:44px;margin-top:4px;color:var(--blue-t,var(--blue));font-weight:900;font-size:15px}
.ct-tel{display:flex;align-items:center;gap:8px;height:52px;padding:0 16px;border-radius:16px;border:1.5px solid var(--line);background:var(--card);margin:14px 0 4px}
.ct-tel:focus-within{border-color:var(--blue)}
.ct-tel .cc{font-weight:900;color:var(--muted)}
.ct-tel input{flex:1;min-width:0;height:100%;border:0;background:none;font-size:17px;font-weight:800;color:var(--ink);outline:none}
.ct-set .pbtn{flex:none}""")

# onboarding's own styles are outside @layer app, so the +1 field's padding goes next to them
one(""".onb .unwrap .input{padding:0 44px 0 34px;font-weight:800;font-size:17px}""", """.onb .unwrap .input{padding:0 44px 0 34px;font-weight:800;font-size:17px}
.onb .unwrap.cc .input{padding-left:50px}""")

# ---- 2. the Contacts pill ----------------------------------------------------------------------------
one("""<div class="fhdr"><div class="title">Friends</div><button class="invpill" data-a="sheet" data-x="invite" aria-label="Invite friends">${ic('qr', 18, 2.4)}Invite</button></div>""",
"""<div class="fhdr"><div class="title">Friends</div><div class="fpills"><button class="invpill ctpill" data-a="ctOpen" aria-label="Find friends from your contacts">${ic('users', 18, 2.4)}Contacts</button><button class="invpill" data-a="sheet" data-x="invite" aria-label="Invite friends">${ic('qr', 18, 2.4)}Invite</button></div></div>""")

# ---- 3. a queued sheet opens once the one in front of it has closed ------------------------------------
one("""  else sh.innerHTML = '';
  if (UI.champ || !UI.sheet) delete sh.dataset.open;""",
"""  else sh.innerHTML = '';
  if (UI.champ || !UI.sheet) delete sh.dataset.open;
  if (!UI.champ && !UI.sheet && UI.sheetNext && !UI.sheetHold) sheetNextSoon();""")

# ---- 4. onboarding: the phone step after year/major, and the asks at the end ---------------------------
one("""  const body = step === 'degree' ? onbDegree() : step === 'confirm' ? onbConfirm()""",
"""  const body = step === 'phone' ? onbPhone() : step === 'degree' ? onbDegree() : step === 'confirm' ? onbConfirm()""")
one("""    UI.pl = null; onbGo('people');""", """    UI.pl = null; onbGo('phone');""")
one("""order = ['schedule', 'confirm', 'people', 'degree', 'payoff'];""", """order = ['schedule', 'confirm', 'phone', 'people', 'degree', 'payoff'];""")
one("""if (onb) setTimeout(() => TC.pushAsk('onboarding'), 600); },""", """if (onb) setTimeout(() => onbAsks(), 600); },""")
one("""    save(); render(); setTimeout(() => TC.pushAsk('onboarding'), 600);""", """    save(); render(); setTimeout(() => onbAsks(), 600);""")
one("""if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet.onb = true; else setTimeout(() => TC.pushAsk('onboarding'), 600); }""",
    """if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet.onb = true; else setTimeout(() => onbAsks(), 600); }""")

# ---- 5. the feature ------------------------------------------------------------------------------------
one("""const pushOpenSettings = A.openSettings;""", r"""/* ================================================================================================
   CONNECT CONTACTS (2026-10-30)
   ------------------------------------------------------------------------------------------------
   The address book never leaves the phone: numbers (E.164) and emails (lower-case) are SHA-256'd
   here and only the hashes go to match_contacts(), 1000 a call; names stay on the phone. The
   student's own number goes as one hash to set_my_phone(). sql/termchamp-contacts-2026-10-30.sql.
   Per device (localStorage tc_ct:<user>): connected, the pop-up's 30-day snooze, app opens counted.
   ================================================================================================ */
I.phone = '<rect x="6.5" y="2.5" width="11" height="19" rx="2.6"/><path d="M10.5 18.5h3"/>';
const CT_BATCH = 1000, CT_MAX = 8000, CT_SNOOZE = 30 * 864e5;
const CT_MSG = 'Hey! I’m using TermChamp to plan classes and see when friends are free. Add me: ';
/* The phone preview (localhost): a made-up address book, so the flow can be tapped through. */
const CT_SAMPLE = [['Jordan Rivera', '(805) 555-0101'], ['Priya Patel', '805-555-0102'], ['Sam Lee', '+1 805 555 0103'], ['Chris Nguyen', '8055550104'],
  ['Taylor Brooks', '(619) 555-0105'], ['Mia Chen', '760.555.0106'], ['Alex Kim', '1 (858) 555-0107'], ['Drew Carter', '(805) 555-0108'], ['Riley Morgan', '(415) 555-0109']]
  .map(([n, ph], i) => { const w = n.split(' '); return { contactId: 'sample' + i, name: { display: n, given: w[0], family: w[1] }, phones: [{ number: ph }], emails: [] }; });
TC.ctPlugin = function () { try { return PUSH.native() && window.Capacitor.Plugins ? window.Capacitor.Plugins.Contacts || null : null; } catch (e) { return null; } };
TC.ctPreview = function () { return /^(localhost|127\.0\.0\.1)$/.test(location.hostname); };
TC.ctGo = function (url) { window.location.href = url; };
function ctAvail() { return !!(TC.ctPlugin() || TC.ctPreview()); }
function ctKey() { return 'tc_ct:' + (TC.user ? TC.user.id : ''); }
function ctState() { let o = null; try { o = JSON.parse(localStorage.getItem(ctKey()) || 'null'); } catch (e) {} return o && typeof o === 'object' ? o : {}; }
function ctSet(patch) { const o = Object.assign(ctState(), patch); try { localStorage.setItem(ctKey(), JSON.stringify(o)); } catch (e) {} return o; }
function ctE164(raw) {
  let t = String(raw || '').trim().replace(/\s*(ext\.?|x|#|;|,).*$/i, ''); if (!t) return '';
  let d = t.replace(/\D/g, '');
  if (t[0] === '+') return d.length >= 8 && d.length <= 15 ? '+' + d : '';
  if (d.startsWith('011')) d = d.slice(3); else if (d.startsWith('00')) d = d.slice(2); else if (d.length === 10) return '+1' + d; else if (d.length === 11 && d[0] === '1') return '+' + d; else return '';
  return d.length >= 8 && d.length <= 15 ? '+' + d : '';
}
function ctEmail(raw) { const e = String(raw || '').trim().toLowerCase(); return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e) ? e : ''; }
async function ctSha(t) { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join(''); }
const ctMissing = e => !!e && (e.code === 'PGRST202' || e.status === 404 || e.code === '42883' || /could not find the function/i.test(e.message || ''));
function ctName(c) { const n = c && c.name || {}; return String(n.display || [n.given, n.family].filter(Boolean).join(' ') || '').trim(); }
function ctShowPhone(e) { const m = /^\+1(\d{3})(\d{3})(\d{4})$/.exec(e); return m ? `(${m[1]}) ${m[2]}-${m[3]}` : e; }
/* Read the address book: names and numbers stay here; a hash → contact map goes with them. */
async function ctRead() {
  const plug = TC.ctPlugin();
  let list;
  if (plug) { const r = await plug.getContacts({ projection: { name: true, phones: true, emails: true } }); list = (r && r.contacts) || []; }
  else list = CT_SAMPLE;
  const people = [], phoneH = [], mailH = [], byHash = {}, seenPhone = new Set();
  for (const c of list) {
    const phones = [...new Set((c.phones || []).map(x => ctE164(x && x.number)).filter(Boolean))];
    const mails = [...new Set((c.emails || []).map(x => ctEmail(x && x.address)).filter(Boolean))];
    if (!phones.length && !mails.length) continue;
    const name = ctName(c) || (phones[0] ? ctShowPhone(phones[0]) : mails[0]);
    const k = people.length; people.push({ k, name, phone: phones.find(x => !seenPhone.has(x)) || '', hit: false });
    phones.forEach(x => seenPhone.add(x));
    for (const x of phones) { const h = await ctSha(x); (byHash[h] = byHash[h] || []).push(k); phoneH.push(h); }
    for (const x of mails) { const h = await ctSha(x); (byHash[h] = byHash[h] || []).push(k); mailH.push(h); }
  }
  const hashes = [...new Set(phoneH.concat(mailH))].slice(0, CT_MAX);   /* numbers first: they match best */
  return { people, hashes, byHash };
}
/* Load (or reload) the results sheet. A newer load wins; an older one's answer is dropped. */
async function ctLoad() {
  const gen = (UI.ctGen = (UI.ctGen || 0) + 1);
  const st = UI.ct = { busy: 1, rows: [], invite: [], err: '', unavail: false, limited: false, all: (UI.ct && UI.ct.all) || false, invited: (UI.ct && UI.ct.invited) || {} };
  render(true);
  if (TC.phoneSaved === undefined) ctPhoneLoad();
  const plug = TC.ctPlugin();
  try {
    if (plug) {
      let perm = await plug.checkPermissions().catch(() => ({}));
      if (perm.contacts === 'prompt' || perm.contacts === 'prompt-with-rationale') perm = await plug.requestPermissions();
      if (perm.contacts !== 'granted' && perm.contacts !== 'limited') { if (gen !== UI.ctGen) return; ctSet({ on: false }); UI.ct = null; UI.sheet = { type: 'ctConnect', denied: true }; return render(true); }
      st.limited = perm.contacts === 'limited';
    }
    const book = await ctRead(); if (gen !== UI.ctGen) return;
    const rows = {}; let err = null;
    if (book.hashes.length) {
      const sig = book.hashes.length + ':' + book.hashes.slice().sort().join('').length + ':' + book.hashes.slice(0, 3).join('');
      const c = TC.ctCache;
      if (c && c.sig === sig && Date.now() - c.at < 10 * 6e4) c.rows.forEach(r => { rows[r.id] = r; });
      else {
        for (let i = 0; i < book.hashes.length; i += CT_BATCH) {
          let r; try { r = await TC.client().rpc('match_contacts', { hashes: book.hashes.slice(i, i + CT_BATCH) }); } catch (e) { r = { error: e }; }
          if (r.error) { err = r.error; break; }
          (r.data || []).forEach(x => { if (x && x.id && x.id !== TC.user.id) { const o = rows[x.id] || (rows[x.id] = Object.assign({}, x, { matched: [] })); o.matched = o.matched.concat(x.matched || []); } });
        }
        if (!err) TC.ctCache = { sig, at: Date.now(), rows: Object.values(rows) };
      }
    }
    if (gen !== UI.ctGen) return;
    if (err) { if (ctMissing(err)) st.unavail = true; else st.err = /too fast/i.test(err.message || '') ? 'You’ve checked a lot just now. Try again in a bit.' : 'Couldn’t check your contacts — try again.'; }
    Object.values(rows).forEach(x => { (x.matched || []).forEach(h => (book.byHash[h] || []).forEach(k => { book.people[k].hit = true; })); if (!PEOPLE[x.id] || !TC.friends.includes(x.id)) PEOPLE[x.id] = Object.assign(PEOPLE[x.id] || {}, personFrom(x)); });
    const rank = id => ({ '': 0, incoming: 1, sent: 2, friends: 3 })[TC.relation(id)] || 0;
    st.rows = Object.keys(rows).sort((a, b) => rank(a) - rank(b) || PEOPLE[a].name.localeCompare(PEOPLE[b].name));
    st.invite = book.people.filter(x => !x.hit && x.phone).sort((a, b) => a.name.localeCompare(b.name));
  } catch (e) {
    if (gen !== UI.ctGen) return;
    st.err = 'Couldn’t read your contacts — try again.';
  }
  st.busy = 0; render(true);
}
async function ctPhoneLoad() {
  if (!TC.user || ctPhoneLoad.on || Date.now() - (ctPhoneLoad.at || 0) < 30000) return; ctPhoneLoad.on = 1; ctPhoneLoad.at = Date.now();
  let r; try { r = await TC.client().rpc('my_phone_saved'); } catch (e) { r = { error: e }; }
  ctPhoneLoad.on = 0;
  TC.phoneSaved = r.error ? (ctMissing(r.error) ? null : undefined) : r.data === true;
  if (TC.phoneSaved !== undefined) render(true);
}
function ctLast4() { try { return localStorage.getItem('tc_ct_last4:' + (TC.user ? TC.user.id : '')) || ''; } catch (e) { return ''; } }
/* The pop-up: once, and only where Connect can work (the iPhone app, or the preview). */
function ctAsk(why) {
  if (!TC.user || TC.phase !== 'ok' || !ctAvail() || UI.sheet || UI.champ) return false;
  const st = ctState(); if (st.on || Date.now() < (+st.snooze || 0)) return false;
  ctSet({ snooze: Date.now() + CT_SNOOZE, asked: Date.now(), why });   /* closing it any way counts as "Not now" */
  UI.ct = null; UI.sheet = { type: 'ctConnect', pop: true }; render(true); return true;
}
async function onbAsks() {
  try { await TC.pushAsk('onboarding'); } catch (e) {}
  if (UI.sheet && UI.sheet.type === 'pushAsk') UI.sheetNext = 'ctAsk'; else ctAsk('onboarding');
}
function sheetNextSoon() { const k = UI.sheetNext; UI.sheetNext = null; setTimeout(() => { if (k === 'ctAsk') ctAsk('onboarding'); }, 450); }
/* Students who already had an account: the 2nd app open on, on Home, with nothing else open. */
let ctCounted = false;
function ctLater() {
  if (!TC.user || TC.phase !== 'ok') return;
  const st = ctCounted ? ctState() : ctSet({ n: (+ctState().n || 0) + 1 }); ctCounted = true;
  if ((+st.n || 0) < 2 || st.on || Date.now() < (+st.snooze || 0) || !ctAvail()) return;
  setTimeout(() => { const e = cur(); if (S.tab === 'home' && e && e.s === 'home' && !S.stack.home.some(x => x.s === 'onb') && !UI.sheetNext) ctAsk('later'); }, 2500);
}
{ const pal = TC.pushAfterLoad; TC.pushAfterLoad = async function () { const r = await pal.apply(this, arguments); try { ctLater(); } catch (e) {} return r; }; }
{ const pa = A.pushAllow; A.pushAllow = async function () { UI.sheetHold = 1; try { return await pa.apply(this, arguments); } finally { UI.sheetHold = 0; if (UI.sheetNext && !UI.sheet && !UI.champ) sheetNextSoon(); } }; }

SHEETS.ctConnect = sh => {
  const note = sh.web ? 'Contacts sync is in the iPhone app.' : sh.denied ? 'Contacts are off for TermChamp. Turn them on in your iPhone’s Settings › TermChamp › Contacts.' : '';
  return `${sh.pop ? '' : `<div class="row sb"><h3>Connect contacts</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>`}
 <div style="text-align:center"><div class="ct-tile">${ic('users', 34, 2.2)}</div><h3>Find your friends</h3><p class="muted b" style="font-size:14.5px;line-height:1.45;margin:6px 4px 16px">See who in your contacts is already on TermChamp.</p></div>
 ${note ? `<div class="ct-note" role="status" id="ctNote">${esc(note)}</div>` : ''}
 <div style="display:grid;gap:8px"><button class="btn" data-a="ctConnect">Connect contacts</button>${sh.pop ? '<button class="btn ghost" data-a="ctNotNow">Not now</button>' : ''}</div>
 <div class="muted b ct-fine">You can turn this off any time in Settings.</div>`;
};
SHEETS.ctResults = () => {
  const st = UI.ct || { busy: 1, rows: [], invite: [] };
  const btn = id => { const rel = TC.relation(id);
    return rel === 'friends' ? '<span class="pbtn done">Friends</span>' : rel === 'incoming' ? `<button class="pbtn pink" data-a="acceptReq" data-x="${esc(id)}">Accept</button>`
      : rel === 'sent' ? `<button class="pbtn done" data-a="addFriend" data-x="${esc(id)}" aria-label="Cancel friend request to ${esc(PEOPLE[id].name)}">Requested</button>` : `<button class="pbtn pink" data-a="addFriend" data-x="${esc(id)}" aria-label="Add ${esc(PEOPLE[id].name)}">Add</button>`; };
  const addable = (st.rows || []).filter(id => TC.relation(id) === '').length;
  const on = st.unavail ? '<div class="ct-note" role="status">Contact matching isn’t available yet.</div>'
    : `<div class="ct-h"><span>On TermChamp · ${st.rows.length}</span>${addable > 1 ? `<button class="pbtn pink" data-a="ctAddAll" ${UI.busy.ctAll ? 'disabled' : ''}>${UI.busy.ctAll ? 'Adding…' : 'Add all'}</button>` : ''}</div>
 ${st.rows.length ? st.rows.map(id => { const p = PEOPLE[id]; return `<div class="row ct-row">${pav(id, 44, 15)}<div class="grow"><div class="b nm">${esc(p.name)}</div>${p.handle ? `<div class="muted b" style="font-size:13px">@${esc(p.handle)}</div>` : ''}</div>${btn(id)}</div>`; }).join('')
      : '<div class="muted b" style="font-size:14px;padding:4px 0 8px">None of your contacts are on TermChamp yet. Invite a few below.</div>'}`;
  const mine = TC.phoneSaved === false ? `<button class="ct-mine" data-a="ctPhoneSheet" data-x="ctResults">${ic('phone', 18, 2.3)}<span class="grow">Add your number so friends can find you too</span>${ic('chevR', 16, 2.6)}</button>` : '';
  const shown = st.all ? st.invite : st.invite.slice(0, 5);
  const inv = `<div class="ct-h"><span>Invite · ${st.invite.length}</span></div>
 ${shown.map(c => { const done = st.invited && st.invited[c.phone]; return `<div class="row ct-row"><span class="ct-ini" style="background:${colorFor(c.name)}">${esc(initialsOf(c.name))}</span><div class="grow"><div class="b nm">${esc(c.name)}</div></div><button class="pbtn ${done ? 'done' : ''}" data-a="ctInvite" data-x="${c.k}" aria-label="Invite ${esc(c.name)}">${done ? 'Invited' : 'Invite'}</button></div>`; }).join('')}
 ${!st.all && st.invite.length > 5 ? `<button class="ct-all" data-a="ctAll">See all ${st.invite.length}</button>` : ''}`;
  return `<div class="row sb"><h3>Your contacts</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="ct">${st.busy ? loadingCard('Checking your contacts…') : st.err ? `<div class="tc-err" role="alert">${esc(st.err)}</div><button class="btn soft" style="margin-top:8px" data-a="ctRetry">Try again</button>` + (st.invite.length ? inv : '')
    : on + mine + (st.limited ? '<div class="muted b" style="font-size:12.5px;line-height:1.4;margin-top:8px">You shared some of your contacts. Change which in your iPhone’s Settings › TermChamp › Contacts.</div>' : '') + (st.invite.length ? inv : '')}</div>`;
};
/* Your own number: the sign-up step and this sheet (from the results row and Settings). */
function ctTelField(id, v) {
  return `<label class="ct-tel"><span class="cc" aria-hidden="true">+1</span><input id="${id}" data-in="ctPhone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(805) 555-0134" aria-label="Your phone number" value="${esc(v || '')}" maxlength="20"></label>`;
}
SHEETS.ctPhone = sh => `<form data-submit="ctPhone"><div class="row sb"><h3>Help friends find you</h3><button type="button" class="xbtn" data-a="ctPhoneBack" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="muted b" style="font-size:14px;line-height:1.45;margin-top:4px">Friends who have your number saved will see you on TermChamp.</div>
 ${ctTelField('ctPhoneIn', UI.ctPhoneVal)}
 <div class="tc-err" role="alert" style="${UI.ctPhoneErr ? '' : 'display:none'}">${esc(UI.ctPhoneErr || '')}</div>
 <div style="display:grid;gap:8px;margin-top:12px"><button class="btn" ${UI.busy.ctPhone ? 'disabled' : ''}>${UI.busy.ctPhone ? 'Saving…' : 'Continue'}</button><button type="button" class="btn ghost" data-a="ctPhoneBack">Skip</button></div>
 <div class="muted b ct-fine">Only used to find friends. Never shown on your profile.</div></form>`;
function onbPhone() {
  const saved = TC.phoneSaved === true;
  return `<form class="scr" data-submit="ctPhoneOnb" novalidate>${onbTop({ progress: 2 })}<div class="body">
    <div class="stack"><div class="onb-ico">${ic('users', 36, 2.2)}</div><h1>Help friends find you</h1><p class="lead">Friends who have your number saved will see you on TermChamp.</p></div>
    ${saved ? `<div class="banner" role="status">${ONB_I.check}Your number is saved</div>` : `<div class="field"><label class="label" for="ob-phone">Phone number</label><div class="unwrap cc"><span class="at" aria-hidden="true">+1</span><input class="input" id="ob-phone" data-in="ctPhone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(805) 555-0134" maxlength="20" value="${esc(UI.ctPhoneVal || '')}"></div>
    <div class="hint bad" role="alert" id="ob-phoneerr">${esc(UI.ctPhoneErr || '')}</div></div>`}
    <div class="lock"><span class="dot">${ONB_I.lock}</span>Only used to find friends. Never shown on your profile.</div></div>
    <div class="foot"><button class="btn" type="submit" ${UI.busy.ctPhone ? 'disabled' : ''}>${UI.busy.ctPhone ? 'Saving…' : 'Continue'}</button>
    <button type="button" class="ghost" data-a="ctPhoneSkip">Skip</button></div></form>`;
}
document.addEventListener('input', ev => { if (ev.target && ev.target.dataset && ev.target.dataset.in === 'ctPhone') UI.ctPhoneVal = ev.target.value; });
/* '' = nothing typed; null = not a number; otherwise E.164 */
function ctMyE164(v) { const t = String(v || '').trim(); if (!t) return ''; const d = t.replace(/\D/g, ''); return d.length === 10 ? '+1' + d : d.length === 11 && d[0] === '1' ? '+' + d : null; }
async function ctSaveMine(v) {
  const e = ctMyE164(v); if (e === null) return { err: 'Enter a 10-digit US number, like (805) 555-0134.' };
  let r; try { r = await TC.client().rpc('set_my_phone', { p_hash: await ctSha(e) }); } catch (x) { r = { error: x }; }
  if (r.error) return ctMissing(r.error) ? { missing: 1 } : { err: r.error.code === '23505' ? 'That number is already on another TermChamp account.' : /too fast/i.test(r.error.message || '') ? 'Too many changes today. Try again tomorrow.' : 'Couldn’t save your number — try again.' };
  TC.phoneSaved = true; TC.ctCache = null; try { localStorage.setItem('tc_ct_last4:' + TC.user.id, e.slice(-4)); } catch (x) {}
  return { ok: 1 };
}
SUBMIT.ctPhoneOnb = async () => {
  if (UI.busy.ctPhone) return;
  const v = (document.getElementById('ob-phone') || {}).value || UI.ctPhoneVal || '';
  if (TC.phoneSaved === true || !String(v).trim()) { UI.ctPhoneErr = ''; return onbGo('people'); }
  UI.busy.ctPhone = 1; UI.ctPhoneErr = ''; render(true);
  const r = await ctSaveMine(v); UI.busy.ctPhone = 0;
  if (r.err) { UI.ctPhoneErr = r.err; return render(true); }
  UI.ctPhoneVal = ''; if (r.missing) toast('Saving numbers isn’t switched on yet — add it later in Settings'); onbGo('people');
};
SUBMIT.ctPhone = async () => {
  if (UI.busy.ctPhone) return;
  const v = (document.getElementById('ctPhoneIn') || {}).value || UI.ctPhoneVal || '';
  UI.busy.ctPhone = 1; UI.ctPhoneErr = ''; render(true);
  const r = String(v).trim() ? await ctSaveMine(v) : { err: 'Enter your number, or tap Skip.' }; UI.busy.ctPhone = 0;
  if (r.err || r.missing) { UI.ctPhoneErr = r.err || 'Saving numbers isn’t switched on yet.'; return render(true); }
  UI.ctPhoneVal = ''; toast('Number saved. Friends who have it can find you.'); A.ctPhoneBack();
};

Object.assign(A, {
  ctOpen: () => {
    UI.champ = false;
    if (ctAvail() && ctState().on) { UI.sheet = { type: 'ctResults' }; return ctLoad(); }
    UI.ct = null; UI.sheet = { type: 'ctConnect' }; render(true);
  },
  ctConnect: async () => {
    const sh = UI.sheet || {};
    if (!ctAvail()) { UI.sheet = Object.assign({}, sh, { type: 'ctConnect', web: true }); return render(true); }
    const plug = TC.ctPlugin();
    if (plug) {
      let perm; try { perm = await plug.requestPermissions(); } catch (e) { perm = {}; }
      if (perm.contacts !== 'granted' && perm.contacts !== 'limited') { UI.sheet = Object.assign({}, sh, { type: 'ctConnect', denied: true }); return render(true); }
    }
    ctSet({ on: true }); UI.sheet = { type: 'ctResults' }; ctLoad();
  },
  ctNotNow: () => { ctSet({ snooze: Date.now() + CT_SNOOZE }); A.closeSheet(); },
  ctRetry: () => { TC.ctCache = null; ctLoad(); },
  ctAll: () => { if (UI.ct) UI.ct.all = true; render(true); },
  ctAddAll: async () => {
    if (UI.busy.ctAll || !UI.ct) return;
    const ids = UI.ct.rows.filter(id => TC.relation(id) === ''); UI.busy.ctAll = 1; render(true);
    let n = 0; for (const id of ids) { let okR = false; try { okR = await TC.sendRequest(id); } catch (e) {} if (!okR) break; n++; render(true); }
    UI.busy.ctAll = 0; if (n) toast(`Sent ${n} friend request${n === 1 ? '' : 's'}`); render(true);
  },
  ctInvite: k => {
    const c = UI.ct && UI.ct.invite.find(x => String(x.k) === String(k)); if (!c) return;
    const ios = PUSH.native() || /iP(hone|ad|od)/.test(navigator.userAgent || '');
    TC.ctGo('sms:' + c.phone + (ios ? '&' : '?') + 'body=' + encodeURIComponent(CT_MSG + inviteUrl()));
    UI.ct.invited[c.phone] = 1; render(true);
  },
  ctPhoneSheet: ret => { UI.ctPhoneErr = ''; UI.sheet = { type: 'ctPhone', ret: ret || '' }; render(true); setTimeout(() => { const el = document.getElementById('ctPhoneIn'); if (el) try { el.focus({ preventScroll: true }); } catch (e) {} }, 60); },
  ctPhoneBack: () => { const ret = UI.sheet && UI.sheet.ret; UI.ctPhoneErr = ''; if (ret === 'ctResults') { UI.sheet = { type: 'ctResults' }; return render(true); } A.closeSheet(); },
  ctPhoneSkip: () => { UI.ctPhoneErr = ''; UI.ctPhoneVal = ''; onbGo('people'); },
  ctPhoneRemove: async () => {
    if (UI.busy.ctPhone) return; UI.busy.ctPhone = 1; render(true);
    let r; try { r = await TC.client().rpc('set_my_phone', { p_hash: '' }); } catch (e) { r = { error: e }; }
    UI.busy.ctPhone = 0;
    if (r.error) toast('Couldn’t remove your number — try again');
    else { TC.phoneSaved = false; TC.ctCache = null; try { localStorage.removeItem('tc_ct_last4:' + TC.user.id); } catch (e) {} toast('Number removed'); }
    render(true);
  },
  ctForget: () => { ctSet({ on: false }); TC.ctCache = null; UI.ct = null; render(true); toast(TC.ctPlugin() ? 'Contacts disconnected. To remove access too, turn off Contacts for TermChamp in iPhone Settings.' : 'Contacts disconnected'); }
});
/* Settings › Contacts */
function ctSettings() {
  if (TC.phoneSaved === undefined) ctPhoneLoad();
  const ps = TC.phoneSaved, l4 = ctLast4(), on = ctState().on;
  const phone = `<div class="row sb tc-row ct-set" style="gap:12px"><div><div class="b" style="font-size:15px">Your phone number</div><div class="muted b" style="font-size:12.5px;line-height:1.4">${ps === undefined ? 'Checking…' : ps === null ? 'Not available yet' : ps ? (l4 ? 'Added · ending in ' + esc(l4) : 'Added') : 'Not added'}</div></div>${ps === true ? `<button class="pbtn" data-a="ctPhoneRemove" ${UI.busy.ctPhone ? 'disabled' : ''}>Remove</button>` : ps === false ? '<button class="pbtn pink" data-a="ctPhoneSheet">Add</button>' : ''}</div>`;
  const book = `<div class="row sb tc-row ct-set" style="gap:12px"><div><div class="b" style="font-size:15px">Find friends from contacts</div><div class="muted b" style="font-size:12.5px;line-height:1.4">${on ? 'Connected on this phone' : 'Not connected'}</div></div>${on ? '<button class="pbtn" data-a="ctForget">Turn off</button>' : '<button class="pbtn" data-a="ctOpen">Connect</button>'}</div>`;
  return phone + book + '<div class="muted b" style="font-size:12.5px;line-height:1.45;margin-top:8px">Your number is only used so friends who have it saved can find you. It’s never shown on your profile. Your contacts stay on your phone.</div>';
}
const pushOpenSettings = A.openSettings;""")

# ---- 6. Settings › Contacts, under Notifications ---------------------------------------------------------
one(""" ${sectionCard('Notifications', pushSettings())}""", """ ${sectionCard('Notifications', pushSettings())}
 ${sectionCard('Contacts', ctSettings())}""")

p.write_text(s); print(p, 'contacts: applied')
