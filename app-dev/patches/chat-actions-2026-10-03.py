#!/usr/bin/env python3
"""Chats: like a message, delete a message or a whole chat for yourself, report a message, and class /
professor cards (Tate, 2026-10-03: "make it so i can like messages, i can delete messages on my side. i
can delete conversations … we have to make it so you can share classes and professors and a small
preview shows in chat instead of this" — on a thread of grey "Shared class" / "Shared professor" bubbles).

Messages
- Hold a message (or right-click in the Desktop preview) for its actions: Like / Unlike, Copy, Delete for
  me, and Report (someone else's message only). Double-tap a message to like it.
- A liked message carries a small heart under it (pink if you liked it; a number when more than one
  person did). Tapping the heart likes / unlikes.
- Delete for me hides it for you only (message_hides). The other person still has it.
- Report files the existing reports row (kind 'message', a reason, and the message's words in `note`, because a
  moderator can't read a chat they aren't in and the sender could delete it).

Chats
- "⋯" in a chat's header, or holding a chat in the list → Delete chat. It is removed for you only
  (conversation_clears; the other person can't tell). A new message brings it back with just the new
  messages, like Instagram.

Class and professor cards
- A shared class shows as a card: the code (and section), the class's title, who and when if the sender
  picked a section, its seats **now** (never the number from when it was sent), and "See the class".
- A shared professor shows their name and their rating **now** ("No ratings yet" when there is none) and
  opens their page. Desktop-sent cards work too (their key is "name|dept").
- Send one from a class page or a professor page (the share button next to Save): pick a friend or a group.
- The chat list reads "Shared BUS 3431" / "Shared Ada Examplewood", not "Shared class".
- Message on a friend's page opened from your chat with them goes back to that chat instead of stacking a second copy.
- Your own message never shows twice when its realtime echo lands before the send returns.

Needs sql/professify-chat-likes-hides.sql for likes and deletes. Until it runs, those actions stay out
of the menus (Copy, Report, cards and sending still work).

Applies after day-column-tap-2026-10-03.py.
Usage: python3 chat-actions-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function msgVisible' in s: sys.exit('already patched')

MODULE = r"""/* ================= chats: likes, delete for me, delete a chat, report, cards (Tate, 2026-10-03) =================
   The three tables come from sql/professify-chat-likes-hides.sql. Until it runs, Like and the two
   deletes stay out of the menus; nothing else depends on it. */
TC.likes = {}; TC.hidden = new Set(); TC.clears = {}; TC.chatX = { on: null };
function missingTable(e) { return !!e && (/PGRST205|42P01/.test(String(e.code || '')) || /does not exist|schema cache/i.test(String(e.message || ''))); }
function chatXRead(clr, hid) {
  if ((clr && missingTable(clr.error)) || (hid && missingTable(hid.error))) { TC.chatX.on = false; return; }
  if (clr && !clr.error) { TC.clears = Object.fromEntries((clr.data || []).map(r => [r.conversation_id, r.cleared_at])); TC.chatX.on = true; }
  if (hid && !hid.error) TC.hidden = new Set((hid.data || []).map(r => String(r.message_id)));
}
/* What you still see: not hidden by you, and not from before you deleted the chat. */
function msgVisible(m) { if (TC.hidden.has(String(m.id))) return false; const c = TC.clears[m.conversation_id]; return !c || new Date(m.created_at) > new Date(c); }
function chatCleared(t) { const c = TC.clears[t.id]; return !!c && new Date(t.last_at) <= new Date(c); }
function lastVisible(cid) { const r = TC.rows[cid] || []; for (let i = r.length - 1; i >= 0; i--) if (msgVisible(r[i])) return r[i]; return null; }
async function loadLikes(cid) {
  if (TC.chatX.on === false) return;
  const ids = (TC.rows[cid] || []).slice(-100).map(m => m.id); if (!ids.length) return;
  const r = await TC.client().from('message_likes').select('message_id,user_id').in('message_id', ids);
  if (r.error) { if (missingTable(r.error)) { TC.chatX.on = false; render(true); } return; }
  const L = {}; (r.data || []).forEach(x => { (L[String(x.message_id)] = L[String(x.message_id)] || []).push(x.user_id); });
  const was = TC.likes[cid] || {}; Object.keys(was).forEach(k => { if (UI.busy['lk' + k]) L[k] = was[k]; });   /* a tap still in flight wins */
  TC.likes[cid] = L; TC.chatX.on = true; render(true);
}
const ownKey = (o, k) => k != null && k !== '' && Object.prototype.hasOwnProperty.call(o, k);
/* A professor who isn't teaching this term has no PROFS entry; their PolyRatings row still exists. */
function prRating(pl) {
  const [kn, kd] = String(pl.key || '').split('|'), k = profKeyOf(pl.name || kn || ''), dept = String(kd || '').trim().toLowerCase();
  if (!k || !PR_LIST) return null;
  let hits = PR_LIST.filter(p => p && typeof p.overallRating === 'number' && +p.numEvals > 0 && profKeyOf(((p.firstName || '') + ' ' + (p.lastName || '')).trim()) === k);
  if (dept) hits = hits.filter(p => String(p.department || '').trim().toLowerCase() === dept);
  /* the same name in two departments, and nothing to tell them apart: show no one's number */
  if (!hits.length || new Set(hits.map(p => String(p.department || '').trim().toLowerCase())).size > 1) return null;
  const p = hits.sort((a, b) => (b.numEvals || 0) - (a.numEvals || 0))[0];
  return { r: Math.round((+p.overallRating / 4 * 5) * 100) / 100, count: +p.numEvals || 0, name: ((p.firstName || '') + ' ' + (p.lastName || '')).trim() };
}
function msgLikes(cid, m) {
  const who = (TC.likes[cid] || {})[String(m.id)] || []; if (!who.length) return '';
  const me = TC.user.id, names = who.map(u => u === me ? 'you' : nameOf(u).split(' ')[0]);
  return `<button class="mlk ${m.sender === me ? 'me' : ''} ${who.includes(me) ? 'on' : ''}" data-a="likeMsg" data-x="${esc(String(m.id))}" aria-label="Liked by ${esc(names.join(', '))}">${ic('heart', 13, 2.4, 'currentColor')}${who.length > 1 ? `<span>${who.length}</span>` : ''}</button>`;
}
/* A shared class or professor, read NOW from live data — never the numbers from when it was sent. */
function cardProf(pl) { return [pl.pkey, String(pl.key || '').split('|')[0], profKeyOf(pl.name)].find(k => ownKey(PROFS, k)) || ''; }
function msgCard(m) {
  const pl = m.payload || {};
  if (m.kind === 'class' && pl.code) {
    /* the seats are read now, and only from that same class's section: a CRN from another term can be a different class */
    const code = canonCode(pl.code) || String(pl.code), k = pl.crn != null ? String(pl.crn).trim() : '', s = ownKey(SEC, k) && SEC[k].code === code ? SEC[k] : null;
    const sub = [COURSES[code] ? COURSES[code].title : pl.name, pl.prof, pl.days].filter(Boolean).map(esc).join(' · ');
    if (!canonCode(pl.code)) return `<div class="mcc"><span class="mcc-k">Class</span><b>${esc(String(pl.code))}</b>${sub ? `<span class="mcc-s">${sub}</span>` : ''}</div>`;
    return `<button class="mcc" data-a="openClass" data-x="${esc(code)}"><span class="mcc-k">Class</span><b>${esc(code)}${pl.section ? ' · ' + esc(secLabel(pl.section)) : ''}</b>${sub ? `<span class="mcc-s">${sub}</span>` : ''}${s ? `<span class="mcc-s b">${secSeatText(s)}</span>` : ''}<span class="mcc-go">See the class ${ic('chevR', 14, 2.6)}</span></button>`;
  }
  if (m.kind === 'professor' && (pl.key || pl.name || pl.pkey)) {
    const pk = cardProf(pl), pr = pk ? null : prRating(pl), r = pk ? ratingOf(pk) : pr ? pr.r : null, n = pk ? PROFS[pk].count : pr ? pr.count : 0;
    const nm = esc((pk && PROFS[pk].name) || (pr && pr.name) || pl.name || 'A professor');
    const wait = !TC.profsLoaded && !PR_LIST ? (TC.err.poly ? 'Ratings didn’t load' : 'Loading the rating…') : '';
    const line = r != null ? `${starI(13, rateTone(r).star)}<span class="rt-${rateTone(r).k}" style="color:${rateTone(r).ink}">${r.toFixed(1)}</span><span class="muted">&nbsp;· ${nRatings(n)}</span>`
      : wait ? `<span class="muted">${wait}</span>` : pk ? '<span class="muted">No ratings yet</span>' : '<span class="muted">We don’t have a rating for them</span>';
    return pk ? `<button class="mcc prof" data-a="openProf" data-x="${esc(pk)}"><span class="mcc-k">Professor</span><b>${nm}</b><span class="mcc-s row b" style="gap:4px">${line}</span><span class="mcc-go">See their page ${ic('chevR', 14, 2.6)}</span></button>`
      : `<div class="mcc prof"><span class="mcc-k">Professor</span><b>${nm}</b><span class="mcc-s row b" style="gap:4px">${line}</span></div>`;
  }
  return '';
}
function chatOf(cid) { return TC.threads.find(t => t.id === cid); }
function msgOf(mid) { const cid = cur().p && cur().p.id; return { cid, m: (TC.rows[cid] || []).find(x => String(x.id) === String(mid)) }; }
SHEETS.msgAct = ({ mid }) => {
  const { cid, m } = msgOf(mid); if (!m) return '';
  const me = TC.user.id, mine = m.sender === me, on = TC.chatX.on !== false, t = chatOf(cid);
  const liked = ((TC.likes[cid] || {})[String(m.id)] || []).includes(me), k = esc(String(m.id));
  const still = t && t.kind === 'direct' ? (threadOther(t) ? esc(nameOf(threadOther(t)).split(' ')[0]) + ' still sees it' : 'They still see it') : 'Everyone else still sees it';
  const prev = esc(msgText(m).slice(0, 160));
  return `<div class="row sb"><h3>Message</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="mprev ${mine ? 'me' : ''}">${prev || '…'}</div>
 <div class="card list mact">${on ? `<button class="li" data-a="likeMsg" data-x="${k}">${ic('heart', 20, 2.2, liked ? 'currentColor' : 'none')}<span class="grow b">${liked ? 'Unlike' : 'Like'}</span></button>` : ''}
 ${m.body ? `<button class="li" data-a="copyMsg" data-x="${k}">${ic('copy', 20, 2.2)}<span class="grow b">Copy</span></button>` : ''}
 ${on ? `<button class="li" data-a="hideMsg" data-x="${k}">${ic('trash', 20, 2.2)}<span class="grow"><span class="b" style="display:block">Delete for me</span><span class="muted b" style="font-size:12.5px">${still}</span></span></button>` : ''}
 ${!mine ? `<button class="li danger" data-a="reportMsg" data-x="${k}">${ic('flag', 20, 2.2)}<span class="grow b">Report</span></button>` : ''}</div>`;
};
const REPORT_WHY = [['harassment', 'Harassment or bullying'], ['hate', 'Hate or slurs'], ['threat', 'A threat'], ['sexual', 'Sexual content'], ['private_info', 'Private information'], ['spam', 'Spam'], ['other', 'Something else']];
SHEETS.reportMsg = ({ mid }) => {
  const { m } = msgOf(mid); if (!m) return '';
  return `<div class="row sb"><h3>Report this message</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="muted b" style="font-size:14px;margin:4px 0 12px">A moderator will see this message and who sent it. ${esc(nameOf(m.sender).split(' ')[0])} won’t know it was you.</div>
 <div class="card list">${REPORT_WHY.map(([k, l]) => `<button class="li" data-a="sendReport" data-x="${k}" data-y="${esc(String(m.id))}"${UI.busy.report ? ' disabled' : ''}><span class="grow b">${l}</span>${ic('chevR', 18)}</button>`).join('')}</div>
 <div class="muted b" style="font-size:12.5px;margin-top:10px">If someone is in danger, call 911. TermChamp is not an emergency service.</div>`;
};
SHEETS.chatAct = ({ cid }) => {
  const t = chatOf(cid); if (!t) return '';
  return `<div class="row sb"><h3>${esc(threadName(t))}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="card list mact">${t.kind === 'direct' && threadOther(t) && TC.friends.includes(threadOther(t)) ? `<button class="li" data-a="openFriend" data-x="${esc(threadOther(t))}">${pav(threadOther(t), 28, 10)}<span class="grow b">See ${esc(nameOf(threadOther(t)).split(' ')[0])}’s page</span>${ic('chevR', 18)}</button>` : ''}
 ${TC.chatX.on !== false ? `<button class="li danger" data-a="chatDelAsk" data-x="${esc(cid)}">${ic('trash', 20, 2.2)}<span class="grow b">Delete chat</span></button>` : '<div class="muted b" style="font-size:13.5px;padding:12px 14px">Deleting chats isn’t switched on yet.</div>'}</div>`;
};
SHEETS.chatDel = ({ cid }) => {
  const t = chatOf(cid); if (!t) return '';
  const who = t.kind === 'direct' && threadOther(t) ? esc(nameOf(threadOther(t)).split(' ')[0]) + ' still has it' : 'Everyone else still has it';
  return `<h3>Delete this chat?</h3>
 <div class="muted b" style="font-size:14.5px;margin:8px 0 16px;line-height:1.4">It’s removed for you only — ${who}. If a new message comes in, the chat comes back with just the new messages.</div>
 <div style="display:grid;gap:8px"><button class="btn" style="background:#DC2626" data-a="delChat" data-x="${esc(cid)}"${UI.busy.delChat ? ' disabled' : ''}>Delete chat</button><button class="btn soft" data-a="closeSheet">Cancel</button></div>`;
};
SHEETS.sendCard = ({ kind, ref }) => {
  const sc = UI.card || {}, isC = kind === 'class', label = isC ? ref : (PROFS[ref] ? PROFS[ref].name : 'this professor');
  const tg = shTargets().map(t => Object.assign({}, t, { a: t.a === 'shareTo' ? 'cardTo' : 'cardToThread' }));
  return `<div class="row sb"><h3>Send ${esc(label)}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="muted b" style="font-size:14px;margin:4px 0 10px">It shows in the chat as a card with ${isC ? 'the class and its seats' : 'their rating'}, read when it’s opened.</div>
 ${tg.length ? tg.map(t => { const done = (sc.sent || {})[t.k], busy = (sc.busy || {})[t.k]; return `<button class="shrow" data-a="${t.a}" data-x="${esc(t.x)}" ${done || busy ? 'disabled' : ''}>${t.av}<span class="grow b">${esc(t.name)}</span><span class="shsend ${done ? 'done' : ''}">${done ? 'Sent' : busy ? 'Sending…' : 'Send'}</span></button>`; }).join('')
   : '<div class="muted b" style="font-size:14px;padding:8px 0">Add friends to send it to them here.</div>'}`;
};
function cardPayload(kind, ref) {
  if (kind === 'class') return { code: ref, name: course(ref).title || '' };
  const P = PROFS[ref]; return P ? { key: ((P.name || '') + '|' + (P.dept || '')).toLowerCase().trim(), pkey: ref, name: P.name || '' } : null;
}
async function cardSend(k, cidOf) {
  const sc = UI.card; if (!sc || sc.busy[k] || sc.sent[k]) return;
  const pl = cardPayload(sc.kind, sc.ref); if (!pl) return;
  sc.busy[k] = 1; render(true);
  const cid = await cidOf(), ok = cid ? await TC.send(cid, null, sc.kind, pl) : false;
  delete sc.busy[k]; if (ok) { sc.sent[k] = 1; toast('Sent'); }
  if (UI.card === sc) render(true);
}
/* Hold a message (or a chat in the list) for its actions; double-tap a message to like it. */
const LP = { t: null, x: 0, y: 0, el: null, held: false, until: 0, opened: 0, tap: { id: null, at: 0 } };
function lpTarget(el) { return el && el.closest ? el.closest('#scroll .msg[data-mid], #fbody .thread[data-x]') : null; }
function lpOpen(el) {
  UI.sheet = el.classList.contains('thread') ? { type: 'chatAct', cid: el.dataset.x } : { type: 'msgAct', mid: el.dataset.mid };
  LP.opened = Date.now();
  const ae = document.activeElement; if (ae && ae.blur && ae.matches && ae.matches('input,textarea')) ae.blur();   /* the keyboard goes down so the sheet shows */
  render(true);
  try { if (navigator.vibrate) navigator.vibrate(10); } catch (e) {}
}
(function () {
  const sc = document.getElementById('scroll'); if (!sc) return;
  const start = (el, x, y) => { clearTimeout(LP.t); LP.held = false; LP.el = el; LP.x = x; LP.y = y; if (el) LP.t = setTimeout(() => { if (LP.el === el) { LP.el = null; LP.held = true; lpOpen(el); } }, 450); };
  const move = (x, y) => { if (LP.el && Math.hypot(x - LP.x, y - LP.y) > 10) { clearTimeout(LP.t); LP.el = null; } };
  /* the click a lift makes comes right after it: while held, and for 350ms after the lift, a click is not a tap */
  const end = () => { clearTimeout(LP.t); LP.el = null; if (LP.held) { LP.held = false; LP.until = Date.now() + 350; } };
  /* Opening the sheet redraws the chat, so the touched bubble leaves the page and its touchend no longer reaches
     #scroll: listen on the touched element itself too. */
  sc.addEventListener('touchstart', e => {
    if (e.touches.length !== 1) return end();
    const tg = e.target; if (tg && tg.addEventListener) { tg.addEventListener('touchend', end, { once: true, passive: true }); tg.addEventListener('touchcancel', end, { once: true, passive: true }); }
    start(lpTarget(e.target), e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  sc.addEventListener('touchmove', e => { if (e.touches.length === 1) move(e.touches[0].clientX, e.touches[0].clientY); }, { passive: true });
  sc.addEventListener('touchend', end, { passive: true }); sc.addEventListener('touchcancel', end, { passive: true });
  sc.addEventListener('mousedown', e => { if (e.button === 0) start(lpTarget(e.target), e.clientX, e.clientY); });
  document.addEventListener('mousemove', e => { if (LP.el) move(e.clientX, e.clientY); });
  document.addEventListener('mouseup', end);
  sc.addEventListener('contextmenu', e => { const el = lpTarget(e.target); if (el) { e.preventDefault(); end(); LP.until = Date.now() + 350; lpOpen(el); } });
  /* window capture runs before the app's own click handling: the click that ends a hold is not a tap,
     and a second tap on the same message within 320ms likes it */
  /* failsafe: any new press, or leaving the app, ends a hold whose lift was lost (alt-tab, a cancelled touch) */
  const unheld = () => { LP.held = false; };
  ['pointerdown', 'mousedown', 'touchstart'].forEach(t => window.addEventListener(t, unheld, { capture: true, passive: true }));
  window.addEventListener('blur', unheld); document.addEventListener('visibilitychange', unheld);
  window.addEventListener('click', e => {
    const now0 = Date.now(), inSheet = e.target.closest && e.target.closest('#sheet');
    if (LP.held || now0 < LP.until || (inSheet && now0 - LP.opened < 400)) { e.stopImmediatePropagation(); e.preventDefault(); return; }
    const el = e.target.closest && e.target.closest('#scroll .msg[data-mid]');
    if (!el || e.target.closest('[data-a]') || TC.chatX.on === false) return;
    const id = el.dataset.mid, now = Date.now();
    if (LP.tap.id === id && now - LP.tap.at < 320) { LP.tap = { id: null, at: 0 }; A.likeMsg(id, null, null, 'dbl'); }
    else LP.tap = { id, at: now };
  }, true);
})();
"""

ACTIONS = r"""  /* chats (2026-10-03) */
  chatMenu: cid => { UI.sheet = { type: 'chatAct', cid }; render(true); },
  chatDelAsk: cid => { UI.sheet = { type: 'chatDel', cid }; render(true); },
  likeMsg: async (mid, y, el, how) => {
    const cid = cur().p && cur().p.id; if (!cid || !TC.user || TC.chatX.on === false) return;
    const me = TC.user.id, k = String(mid), L = TC.likes[cid] = TC.likes[cid] || {}, had = (L[k] || []).includes(me);
    if (how === 'dbl' && had) return;                    // a double-tap only ever likes
    if (UI.busy['lk' + k]) return; UI.busy['lk' + k] = 1;
    L[k] = had ? (L[k] || []).filter(u => u !== me) : (L[k] || []).concat([me]);
    if (UI.sheet && UI.sheet.type === 'msgAct') UI.sheet = null;
    render(true);
    const sb = TC.client(), r = had ? await sb.from('message_likes').delete().eq('message_id', mid).eq('user_id', me) : await sb.from('message_likes').insert({ message_id: mid });
    UI.busy['lk' + k] = 0;
    if (r.error && !(!had && /23505|duplicate/.test(String(r.error.code || '') + String(r.error.message || '')))) {
      const L2 = TC.likes[cid] = TC.likes[cid] || {};   /* loadLikes may have swapped the object meanwhile */
      L2[k] = had ? (L2[k] || []).filter(u => u !== me).concat([me]) : (L2[k] || []).filter(u => u !== me);
      if (missingTable(r.error)) TC.chatX.on = false;
      toast('Couldn’t ' + (had ? 'unlike' : 'like') + ' that — try again'); render(true);
    }
  },
  copyMsg: async mid => { const { m } = msgOf(mid); if (!m || !m.body) return; UI.sheet = null; render(true); try { await navigator.clipboard.writeText(m.body); toast('Copied'); } catch (e) { toast('Couldn’t copy'); } },
  hideMsg: async mid => {
    const { cid, m } = msgOf(mid); if (!m || UI.busy.hide) return; UI.busy.hide = 1;
    const r = await TC.client().from('message_hides').insert({ message_id: m.id }); UI.busy.hide = 0;
    if (r.error && !/23505|duplicate/.test(String(r.error.code || '') + String(r.error.message || ''))) { if (missingTable(r.error)) TC.chatX.on = false; toast('Couldn’t delete that — try again'); return; }
    TC.hidden.add(String(m.id)); UI.sheet = null;
    const t = chatOf(cid); if (t && t.last && String(t.last.id) === String(m.id)) t.last = lastVisible(cid);
    render(true); toast('Deleted for you');
  },
  reportMsg: mid => { UI.sheet = { type: 'reportMsg', mid }; render(true); },
  sendReport: async (reason, mid) => {
    const { m } = msgOf(mid); if (!m || UI.busy.report) return; UI.busy.report = 1; render(true);
    /* the words go with the report: a moderator can't read a chat they aren't in, and the sender could delete it */
    const r = await TC.client().from('reports').insert({ reporter: TC.user.id, kind: 'message', target_id: String(m.id), target_user: m.sender, reason, note: msgText(m).slice(0, 2000) || null });
    UI.busy.report = 0;
    if (r.error) {
      const t = String(r.error.code || '') + ' ' + String(r.error.message || '');
      if (/23505|duplicate|one_per/.test(t)) { UI.sheet = null; render(true); toast('You already reported this — it’s with a moderator'); return; }
      toast(/row-level|42501/.test(t) ? 'You’ve sent a lot of reports this hour — try again later' : 'Couldn’t send the report — try again'); render(true); return;
    }
    UI.sheet = null; render(true); toast('Reported. A moderator will look at it.');
  },
  delChat: async cid => {
    const t = chatOf(cid); if (!t || UI.busy.delChat) return; UI.busy.delChat = 1; render(true);
    /* The newest message's own server time, read now: a phone clock running fast could hide a message sent a moment
       later, and the list's copy can be behind if the live connection slept. */
    const sb = TC.client(), me = TC.user.id;
    const nw = await sb.from('messages').select('created_at').eq('conversation_id', cid).order('created_at', { ascending: false }).limit(1);
    const at = (!nw.error && nw.data && nw.data[0] && nw.data[0].created_at) || t.last_at || new Date().toISOString();
    let r = await sb.from('conversation_clears').update({ cleared_at: at }).eq('conversation_id', cid).eq('user_id', me).select();
    if (!r.error && !(r.data || []).length) r = await sb.from('conversation_clears').insert({ conversation_id: cid, cleared_at: at });
    UI.busy.delChat = 0;
    if (r.error) { if (missingTable(r.error)) TC.chatX.on = false; toast('Couldn’t delete the chat — try again'); render(true); return; }
    TC.clears[cid] = at; t.last = null; UI.sheet = null;
    if (cur().s === 'chat' && cur().p && cur().p.id === cid) back(); else render(true);
    toast('Chat deleted');
  },
  sendCard: (kind, ref) => { if (!TC.user) return; UI.card = { kind, ref, sent: {}, busy: {} }; UI.sheet = { type: 'sendCard', kind, ref }; render(true); },
  cardTo: uid => { if (TC.friends.includes(uid)) cardSend('u:' + uid, () => TC.threadWith(uid)); },
  cardToThread: cid => { if (TC.threads.some(t => t.id === cid)) cardSend('t:' + cid, async () => cid); },
"""

R = [
 # icons
 (" plus:'<path d=\"M12 5v14M5 12h14\"/>',",
  " plus:'<path d=\"M12 5v14M5 12h14\"/>',heart:'<path d=\"M12 20.3s-7.4-4.5-9.2-9.1C1.5 7.8 3.7 4.6 7.1 4.6c2 0 3.5 1.1 4.9 2.9 1.4-1.8 2.9-2.9 4.9-2.9 3.4 0 5.6 3.2 4.3 6.6-1.8 4.6-9.2 9.1-9.2 9.1z\"/>',copy:'<rect x=\"8.5\" y=\"8.5\" width=\"11.5\" height=\"11.5\" rx=\"2.2\"/><path d=\"M15.5 8.5V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7.5a2 2 0 0 0 2 2h2.5\"/>',flag:'<path d=\"M5.5 21V4.5M5.5 4.5h11.5l-2.2 4.2 2.2 4.3H5.5\"/>',dots:'<circle cx=\"5.5\" cy=\"12\" r=\"1.7\"/><circle cx=\"12\" cy=\"12\" r=\"1.7\"/><circle cx=\"18.5\" cy=\"12\" r=\"1.7\"/>',"),
 # loading: clears and hides with the chat list; the last message you can still see
 ("    sb.from('messages').select('conversation_id,sender,kind,body,created_at').in('conversation_id', ids).order('created_at', { ascending: false }).limit(300)\n  ]);\n",
  "    sb.from('messages').select('id,conversation_id,sender,kind,body,payload,created_at').in('conversation_id', ids).order('created_at', { ascending: false }).limit(300),\n"
  "    sb.from('conversation_clears').select('conversation_id,cleared_at'),\n"
  "    sb.from('message_hides').select('message_id').limit(5000)\n  ]);\n  chatXRead(clr, hid);\n"),
 ("  const [convs, memb, last] = await Promise.all([\n", "  const [convs, memb, last, clr, hid] = await Promise.all([\n"),
 ("  ((last && last.data) || []).forEach(m => { if (!lastOf[m.conversation_id]) lastOf[m.conversation_id] = m;",
  "  ((last && last.data) || []).forEach(m => { if (!lastOf[m.conversation_id] && msgVisible(m)) lastOf[m.conversation_id] = m;"),
 ("  TC.rows[cid] = r.data || [];\n  const at = new Date().toISOString();\n",
  "  TC.rows[cid] = r.data || [];\n  loadLikes(cid);\n  const at = new Date().toISOString();\n"),
 # sending any kind
 ("TC.send = async function (cid, body) {\n  const r = await TC.client().from('messages').insert({ conversation_id: cid, sender: TC.user.id, kind: 'text', body, payload: null }).select().single();\n",
  "TC.send = async function (cid, body, kind, payload) {\n  const r = await TC.client().from('messages').insert({ conversation_id: cid, sender: TC.user.id, kind: kind || 'text', body: body == null ? null : body, payload: payload || null }).select().single();\n"),
 # the realtime echo of your own message can land before the insert returns: never show it twice
 ("  (TC.rows[cid] = TC.rows[cid] || []).push(r.data);\n  const t = TC.threads.find(x => x.id === cid); if (t) { t.last = r.data;",
  "  const rows = TC.rows[cid] = TC.rows[cid] || []; if (!rows.some(x => String(x.id) === String(r.data.id))) rows.push(r.data);   /* the realtime echo may be in already */\n  const t = TC.threads.find(x => x.id === cid); if (t) { t.last = r.data;"),
 # the chat list: deleted chats are gone until a new message; previews name what was shared
 ("  const ts = TC.threads.filter(t => t.last || t.kind !== 'direct');",
  "  const ts = TC.threads.filter(t => (t.last || t.kind !== 'direct') && !chatCleared(t));"),
 ("  if (m.kind && m.kind !== 'text') return 'Shared ' + String(m.kind).replace(/_/g, ' ');\n",
  "  if (m.kind === 'class' && m.payload && m.payload.code) return 'Shared ' + m.payload.code;\n"
  "  if (m.kind === 'professor' && m.payload && m.payload.name) return 'Shared ' + m.payload.name;\n"
  "  if (m.kind && m.kind !== 'text') return 'Shared ' + String(m.kind).replace(/_/g, ' ');\n"),
 # the chat: what you still see, holdable bubbles, likes, cards, the ⋯ menu
 ("  const msgs = (rows || []).map(m => {\n", "  const msgs = (rows || []).filter(msgVisible).map(m => {\n"),
 ("    if (shm) return `${sep}<div class=\"msg shm ${mine ? 'me' : ''}\">",
  "    if (shm) return `${sep}<div class=\"msg shm ${mine ? 'me' : ''}\" data-mid=\"${esc(String(m.id))}\">"),
 ("<span>${esc(shm.text || 'Shared a schedule')}</span></button></div>`;\n",
  "<span>${esc(shm.text || 'Shared a schedule')}</span></button></div>${msgLikes(id, m)}`;\n"
  "    const card = msgCard(m);\n"),
 ("    return `${sep}<div class=\"msg ${mine ? 'me' : ''}\">${showWho ? `<span class=\"who\">${esc(nameOf(m.sender).split(' ')[0])}</span>` : ''}${esc(msgText(m))}</div>`;\n",
  "    return `${sep}<div class=\"msg ${mine ? 'me' : ''}${card ? ' mcard' : ''}\" data-mid=\"${esc(String(m.id))}\">${showWho ? `<span class=\"who\">${esc(nameOf(m.sender).split(' ')[0])}</span>` : ''}${card ? card + (m.body ? `<span class=\"mcc-note\">${esc(m.body)}</span>` : '') : esc(msgText(m))}</div>${msgLikes(id, m)}`;\n"),
 ("aria-label=\"Back\">${ic('chevL', 20, 2.4)}</button>${head}</div>`, padTop: 64,",
  "aria-label=\"Back\">${ic('chevL', 20, 2.4)}</button>${head}<button class=\"iconbtn\" style=\"width:38px;height:38px;flex:none\" data-a=\"chatMenu\" data-x=\"${esc(id)}\" aria-label=\"Chat options\">${ic('dots', 20, 2, 'currentColor')}</button></div>`, padTop: 64,"),
 # send a class / a professor from their pages
 ("<button class=\"iconbtn ${isSaved('c:' + code) ? 'on' : ''}\" data-a=\"save\" data-x=\"c:${code}\" aria-label=\"Save\">${ic('bm', 20, 2.2, isSaved('c:' + code) ? 'currentColor' : 'none')}</button></div>",
  "<span class=\"row\" style=\"gap:8px\"><button class=\"iconbtn\" data-a=\"sendCard\" data-x=\"class\" data-y=\"${esc(code)}\" aria-label=\"Send to a friend\">${ic('share', 20, 2.2)}</button><button class=\"iconbtn ${isSaved('c:' + code) ? 'on' : ''}\" data-a=\"save\" data-x=\"c:${code}\" aria-label=\"Save\">${ic('bm', 20, 2.2, isSaved('c:' + code) ? 'currentColor' : 'none')}</button></span></div>"),
 ("<button class=\"iconbtn ${isSaved('p:' + id) ? 'on' : ''}\" data-a=\"save\" data-x=\"p:${esc(id)}\" aria-label=\"Save\">${ic('bm', 20, 2.2, isSaved('p:' + id) ? 'currentColor' : 'none')}</button></div>\n <div class=\"hero purple\">",
  "<span class=\"row\" style=\"gap:8px\"><button class=\"iconbtn\" data-a=\"sendCard\" data-x=\"professor\" data-y=\"${esc(id)}\" aria-label=\"Send to a friend\">${ic('share', 20, 2.2)}</button><button class=\"iconbtn ${isSaved('p:' + id) ? 'on' : ''}\" data-a=\"save\" data-x=\"p:${esc(id)}\" aria-label=\"Save\">${ic('bm', 20, 2.2, isSaved('p:' + id) ? 'currentColor' : 'none')}</button></span></div>\n <div class=\"hero purple\">"),
 # module and actions
 ("const SHEETS = {};\n", "const SHEETS = {};\n" + MODULE),
 # what you've typed survives the redraws a like, a hold or a delete make (they redraw the composer too)
 ("  const ae = document.activeElement, focusId = ae && ae.id && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA') ? ae.id : null,",
  "  { const ci = document.getElementById('chatin'), e = cur(), f = ci && ci.closest('form'); if (f && e && e.s === 'chat' && e.p && f.dataset.x === String(e.p.id)) UI.prefill = { id: e.p.id, text: ci.value }; }\n"
  "  const ae = document.activeElement, focusId = ae && ae.id && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA') ? ae.id : null,"),
 ("  copyLink: async () => {", ACTIONS + "  copyLink: async () => {"),
 # Message on a friend's page you reached from your chat with them goes back to that chat, not a second copy of it
 ("  openChat: id => { UI.champ = false; TC.openThread(id); go('chat', { id }); },",
  "  openChat: id => {\n"
  "    UI.champ = false; TC.openThread(id);\n"
  "    const st = S.stack[S.tab], below = st[st.length - 2];\n"
  "    if (cur().s !== 'chat' && below && below.s === 'chat' && below.p && below.p.id === id) return back();\n"
  "    go('chat', { id });\n"
  "  },"),
 # styles
 (".msg.me{background:var(--blue);color:#fff;align-self:flex-end}\n",
  ".msg.me{background:var(--blue);color:#fff;align-self:flex-end}\n"
  ".msgs .msg{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none;touch-action:manipulation}\n"
  ".mlk{align-self:flex-start;display:inline-flex;align-items:center;gap:3px;margin:-9px 0 0 10px;padding:3px 7px;min-height:24px;border-radius:12px;background:#fff;color:var(--muted);font-size:12px;font-weight:900;box-shadow:0 1px 3px rgba(15,23,42,.14);position:relative;z-index:1}\n"
  ".mlk.me{align-self:flex-end;margin:-9px 10px 0 0}\n.mlk.on{color:#E11D48}\n"
  ".msg.mcard{padding:4px;background:#fff;color:var(--ink);width:250px;max-width:82%}\n.msg.mcard .who{padding:4px 8px 0}\n"
  ".mcc{display:flex;flex-direction:column;gap:3px;width:100%;text-align:left;padding:10px 12px;border-radius:14px;background:var(--blue-soft)}\n"
  ".mcc.prof{background:#F6F2FF}\n.mcc-k{font-size:11px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}\n"
  ".mcc b{font-size:17px;font-weight:900;color:var(--blue-ink)}\n.mcc.prof b{color:var(--purple-ink)}\n"
  ".mcc-s{font-size:13.5px;font-weight:700;color:var(--ink2);align-items:center}\n.mcc-go{display:inline-flex;align-items:center;gap:2px;margin-top:4px;font-size:13px;font-weight:900;color:var(--blue)}\n"
  ".mcc.prof .mcc-go{color:var(--purple)}\n.mcc-note{display:block;padding:6px 8px 4px;font-size:15px;font-weight:600}\n"
  ".mprev{margin:4px 0 12px;padding:10px 13px;border-radius:16px;background:#fff;font-weight:600;font-size:15px;box-shadow:0 1px 2px rgba(15,23,42,.06)}\n.mprev.me{background:var(--blue);color:#fff}\n"
  ".mact .li{min-height:52px;gap:12px}\n.li.danger{color:#B91C1C}\n"
  "#fbody .thread,#fbody .thread img{-webkit-touch-callout:none;-webkit-user-select:none;user-select:none;-webkit-user-drag:none}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
