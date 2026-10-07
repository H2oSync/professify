#!/usr/bin/env python3
"""Share your week or a plan (Tate, 2026-09-30: "need easy send my schedule / plans"; the pick:
a small share button on your own week and on each plan; the phone's share sheet with a link that
previews as a picture of your real week; and "Send to a friend in TermChamp").

- A Share button in the bar above My Classes and above each plan (A/B/C).
- One sheet: a picture of the week, "Send a link" (the phone's own share sheet — iMessage,
  Snapchat, anything; "Copy the link" where there is none) and a list of friends and group chats.
- The link is the desktop's own: termchamp.com/s?i=<32 random hex>.png&nm=<first>&tm=<term>&add=<id>
  (+ &pl=A for a plan). The picture and the week are uploaded to the public schedule-cards bucket
  under that random name — never the account id — the /s edge function writes the picture into
  the link preview, and the desktop's landing reads the week back. Same bucket, same insert-only
  policy (so NO upsert: an upsert needs an UPDATE policy and 403s, see
  share-upsert-403-2026-09-08.md), the desktop's v2 payload format — nothing to migrate.
- The uploads start when the sheet opens, so the picture is in place by the time iMessage asks
  for it. Re-opening the sheet on an unchanged week reuses the same link and uploads nothing.
- "Send to a friend" sends an ordinary text message ("Here's my Plan A for Fall 2026" + the link):
  messages.kind is CHECK-constrained to text/class/professor/ask, so a new kind would need SQL.
  The phone shows such a message as a card with the picture; the desktop shows the text.
- Nothing is invented: every block is a real section; a class with no set time is listed under
  the grid, an online one says "online", and a plan's missing sections are left out.

Applies after no-grid-folds-2026-09-30.py (17:30).
Usage: python3 share-week-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'SHEETS.share = ' in s: sys.exit('already patched')

JS = r"""
/* ================= share your week or a plan (Tate, 2026-09-30) =================
   "need easy send my schedule / plans". See app-dev/patches/share-week-2026-09-30.py. */
const SC_BUCKET = 'schedule-cards';
const SH_COL = { mine: ['#2563EB', '#D6E4FF', '#1D4ED8'], A: ['#0F766E', '#BDEBE2', '#115E59'], B: ['#C2410C', '#FED7AA', '#9A3412'], C: ['#BE185D', '#F9CFE2', '#9D174D'] };
/* 16 random bytes: the name the picture and the week live under, and the only thing the link carries
   about them. Never the account id — the link gets forwarded. */
function shToken() { const a = new Uint8Array(16); crypto.getRandomValues(a); return Array.from(a, b => b.toString(16).padStart(2, '0')).join(''); }
function shB64url(str) { return btoa(unescape(encodeURIComponent(str))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
const shF = x => String(x == null ? '' : x).replace(/[|~]/g, ' ').trim();
const shHM = m => String(Math.floor(m / 60)).padStart(2, '0') + String(m % 60).padStart(2, '0');
const shTimed = s => !s.async && s.s != null && s.e != null && !!s.days;
/* The desktop's v2 payload ("2~<term>~code|MW1010-1200|prof|section~…"), so its landing reads it with
   the code that already reads every other shared week. An online section carries "=Online" (shown
   as written); a class with no posted time carries nothing, and the landing says "Time TBA". */
function shPayload(term, secs, loose) {
  const rows = secs.map(x => [shF(x.code), x.async ? '=Online' : shTimed(x) ? x.days + shHM(x.s) + '-' + shHM(x.e) : '', shF(x.prof && PROFS[x.prof] ? PROFS[x.prof].name : ''), shF(String(x.sec || '').replace(/\s+Regular\s*$/i, ''))].join('|'))
    .concat((loose || []).map(c => shF(c) + '|||'));
  return shB64url('2~' + shF(term) + '~' + rows.join('~'));
}
function shFirst() { const n = (TC.profile && TC.profile.display_name) || (PEOPLE.me && PEOPLE.me.name) || ''; return n.trim().split(/\s+/)[0] || ''; }
function shLink(id, plan) {
  let q = 'i=' + id + '.png'; const f = shFirst();
  if (f) q += '&nm=' + encodeURIComponent(f);
  q += '&tm=' + encodeURIComponent(CFG.TERM_LABEL);
  if (TC.user && TC.user.id) q += '&add=' + encodeURIComponent(TC.user.id);
  if (plan) q += '&pl=' + plan;
  return String(WEB).replace(/\/+$/, '') + '/s?' + q;
}
const shImg = id => CFG.SUPABASE_URL.replace(/\/+$/, '') + '/storage/v1/object/public/' + SC_BUCKET + '/' + id + '.png';
/* The picture: 1200×1200 (iMessage draws a square about twice as tall as a 1200×630), the real
   week on a grid, anything with no set time listed underneath, never an invented hour. */
function shCard(o) {
  const W = 1200, cv = document.createElement('canvas'); cv.width = cv.height = W; const g = cv.getContext('2d');
  const F = (w, px) => w + ' ' + px + 'px Nunito, system-ui, -apple-system, sans-serif';
  const clip = (t, max) => { t = String(t); if (g.measureText(t).width <= max) return t; while (t.length > 1 && g.measureText(t + '…').width > max) t = t.slice(0, -1); return t + '…'; };
  const rr = (x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };
  const [c1, c2, c3] = o.col;
  g.fillStyle = '#F4F6FB'; g.fillRect(0, 0, W, W);
  g.font = F(900, 40); g.fillStyle = '#16336B'; g.fillText('Term', 64, 92); g.fillStyle = '#2563EB'; g.fillText('Champ', 64 + g.measureText('Term').width, 92);
  g.fillStyle = c1; rr(64, 122, 12, 84, 6); g.fill();
  g.fillStyle = '#0F172A'; g.font = F(900, 56); g.fillText(clip(o.title, W - 170), 96, 178);
  g.fillStyle = '#64748B'; g.font = F(800, 30); g.fillText(clip(o.sub, W - 170), 96, 220);
  const timed = o.secs.filter(shTimed), loose = o.secs.filter(x => !shTimed(x)).map(x => x.code + (x.async ? ' (online)' : '')).concat(o.loose || []);
  const px = 48, py = 256, pw = W - 96, ph = W - py - (loose.length ? 150 : 90);
  g.fillStyle = '#FFFFFF'; rr(px, py, pw, ph, 36); g.fill();
  if (timed.length) {
    const days = DAYS.concat(['S', 'U'].filter(d => timed.some(x => x.days.includes(d))));
    const [a, b] = gridSpan(timed, 240), lab = 96, top = py + 84, bot = py + ph - 34, H = bot - top, cw = (pw - lab - 28) / days.length;
    const Y = m => top + (m - a) / (b - a) * H;
    g.font = F(900, 26); g.textAlign = 'center'; g.fillStyle = '#64748B';
    days.forEach((d, i) => g.fillText((DAYN[d] || d).toUpperCase(), px + lab + cw * i + cw / 2, py + 56));
    g.textAlign = 'right'; g.font = F(800, 22); g.fillStyle = '#94A3B8';
    const step = (b - a) / 60 > 8 ? 120 : 60;
    for (let m = a; m <= b; m += step) g.fillText(hs(m), px + lab - 16, Y(m) + 8);
    days.forEach((d, i) => { g.fillStyle = '#F4F6FB'; rr(px + lab + cw * i + 5, top - 8, cw - 10, H + 16, 16); g.fill(); });
    g.textAlign = 'left';
    timed.forEach(x => [...x.days].forEach(d => {
      const i = days.indexOf(d); if (i < 0) return;
      const bx = px + lab + cw * i + 9, bw = cw - 18, by = Y(x.s), bh = Math.max(Y(x.e) - by - 3, 30);
      g.fillStyle = c2; rr(bx, by, bw, bh, 14); g.fill();
      g.fillStyle = c3; const fs = Math.max(18, Math.min(32, bw / 5.4, bh / 2.4)); g.font = F(900, fs);
      const [sj, nm] = x.code.split(' ');
      g.fillText(clip(sj, bw - 18), bx + 10, by + fs + 6);
      if (bh > fs * 2.3 && nm) g.fillText(clip(nm, bw - 18), bx + 10, by + fs * 2 + 10);
      if (bh > fs * 3.6) { g.font = F(700, Math.round(fs * 0.72)); g.fillText(clip(hs(x.s) + '–' + hs(x.e), bw - 18), bx + 10, by + fs * 3 + 12); }
    }));
  } else {
    g.fillStyle = '#64748B'; g.font = F(800, 34); g.textAlign = 'center'; g.fillText('No set class times', W / 2, py + ph / 2); g.textAlign = 'left';
  }
  if (loose.length) { g.fillStyle = '#334155'; g.font = F(800, 30); g.fillText(clip('No set time: ' + loose.join(', '), W - 128), 64, W - 104); }
  g.fillStyle = '#94A3B8'; g.font = F(800, 26); g.textAlign = 'right'; g.fillText('termchamp.com', W - 64, W - 48); g.textAlign = 'left';
  return cv;
}
/* What gets shared: your own week (every section you're in, plus classes saved with no section),
   or one plan's sections (a section no longer in the term's list is left out, not guessed at). */
function shWhat(what) {
  if (what === 'mine') { const secs = personSecs('me'), loose = (PEOPLE.me.unplaced || []).filter(c => !secs.some(x => x.code === c)); return { secs, loose, plan: null, title: (shFirst() ? shFirst() + '’s' : 'My') + ' week', term: CFG.TERM_LABEL }; }
  return { secs: planSecs(what), loose: [], plan: what, title: (shFirst() ? shFirst() + '’s' : 'My') + ' Plan ' + what, term: CFG.TERM_LABEL + ' Plan ' + what };
}
/* classes, not sections: a lecture and its lab are one class */
const shCount = w => new Set(w.secs.map(x => x.code).concat(w.loose)).size;
UI.shareCache = {};
async function shPrepare(what) {
  if (UI.share && UI.share.url) { try { URL.revokeObjectURL(UI.share.url); } catch (e) {} }
  const w = shWhat(what), sh = UI.share = { what, plan: w.plan, sent: {}, busy: {}, state: 'draw' };
  render(true);   /* the sheet opens at once, saying it's drawing */
  if (!w.secs.length && !w.loose.length) { sh.state = 'empty'; render(true); return; }
  const payload = shPayload(w.term, w.secs, w.loose), key = what + '|' + payload;
  try { await Promise.race([document.fonts && document.fonts.load ? document.fonts.load('900 40px Nunito') : null, new Promise(r => setTimeout(r, 800))]); } catch (e) {}
  if (UI.share !== sh) return;
  const cv = shCard({ title: w.title, sub: CFG.TERM_LABEL + ' · ' + shCount(w) + ' class' + (shCount(w) === 1 ? '' : 'es'), secs: w.secs, loose: w.loose, col: SH_COL[what] || SH_COL.mine });
  const blob = await new Promise(r => { try { cv.toBlob(r, 'image/png'); } catch (e) { r(null); } });
  if (UI.share !== sh) return;
  sh.url = blob ? URL.createObjectURL(blob) : '';
  sh.alt = w.title + ': ' + w.secs.map(x => x.code + ' ' + (x.async ? 'online' : shTimed(x) ? x.days + ' ' + hs(x.s) + '–' + hs(x.e) : 'no set time')).concat(w.loose.map(c => c + ' no set time')).join('; ');
  sh.body = (w.plan ? 'Here’s my Plan ' + w.plan + ' for ' + CFG.TERM_LABEL : 'Here’s my ' + CFG.TERM_LABEL + ' schedule');
  const hit = UI.shareCache[key];
  if (hit) { sh.id = hit; sh.link = shLink(hit, w.plan); sh.state = 'ready'; sh.ready = Promise.resolve(true); render(true); return; }
  if (!blob) { sh.state = 'err'; render(true); return; }
  const id = shToken(); sh.id = id; sh.link = shLink(id, w.plan); sh.state = 'up';
  /* No upsert: the bucket has an INSERT policy only, and an upsert 403s (see the patch notes). */
  const st = TC.client().storage.from(SC_BUCKET);
  sh.ready = Promise.all([st.upload(id + '.png', blob, { contentType: 'image/png' }), st.upload(id + '.json', new Blob([payload], { type: 'application/json' }), { contentType: 'application/json' })])
    .then(rs => { const bad = rs.find(r => r && r.error); if (bad) throw bad.error; UI.shareCache[key] = id; if (UI.share === sh) { sh.state = 'ready'; render(true); } return true; })
    .catch(e => { try { console.warn('[share] upload failed:', (e && e.message) || e); } catch (_) {} if (UI.share === sh) { sh.state = 'err'; render(true); } return false; });
  render(true);
}
/* Who "Send to a friend" offers: group chats and friends, the ones you talk to most recently first. */
function shTargets() {
  const last = {}; TC.threads.forEach(t => { if (t.kind === 'direct') { const o = threadOther(t); if (o) last[o] = t.last_at; } });
  const fr = TC.friends.slice().sort((x, y) => (new Date(last[y] || 0) - new Date(last[x] || 0)) || PEOPLE[x].name.localeCompare(PEOPLE[y].name)).map(id => ({ k: 'u:' + id, a: 'shareTo', x: id, name: PEOPLE[id].name, av: pav(id, 42, 14) }));
  const gr = TC.threads.filter(t => t.kind !== 'direct').slice(0, 4).map(t => ({ k: 't:' + t.id, a: 'shareToThread', x: t.id, name: threadName(t), av: `<span class="sq" style="width:42px;height:42px;background:${colorFor(t.id)};color:var(--ink2);font-size:14px">${esc(initialsOf(threadName(t)))}</span>` }));
  return gr.concat(fr);
}
SHEETS.share = () => {
  const sh = UI.share || {}, P = sh.plan, what = P ? 'Plan ' + P : 'your week';
  const head = `<div class="row sb"><h3>${P ? 'Share Plan ' + P : 'Share your week'}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>`;
  if (sh.state === 'empty') return head + `<div class="empty"><b>Nothing to share yet</b>${P ? 'Add classes to Plan ' + P + ' first.' : 'Add your ' + esc(CFG.TERM_LABEL) + ' classes first.'}</div>`;
  const img = sh.url ? `<img class="shimg" src="${sh.url}" alt="${esc(sh.alt || '')}">` : `<div class="shimg shwait">${loadingCard('Drawing ' + what + '…')}</div>`;
  const err = sh.state === 'err' ? `<div class="tc-err" style="margin:0 0 10px">Couldn’t get the link ready. <button class="link b" style="color:var(--blue)" data-a="shareOpen" data-x="${esc(sh.what)}">Try again</button></div>` : '';
  /* Only once the picture and the week are up: iMessage caches a link's preview for good, so a link
     sent a second too early would stay a bare link. The button is disabled until then, never awaited. */
  const off = !sh.link || sh.state !== 'ready';
  const tg = shTargets();
  return head + img + err
    + `<button class="btn shgo" data-a="shareLink" ${off ? 'disabled' : ''}>${ic('share', 20, 2.4)}${navigator.share ? 'Send a link' : 'Copy the link'}</button>`
    + `<div class="hint" style="margin:8px 2px 0">The link shows this picture in iMessage, Snapchat or anywhere else. Anyone with the link can see these classes.</div>`
    + `<div class="flabel" style="margin:20px 0 4px">Send to a friend in TermChamp</div>`
    + (tg.length ? tg.map(t => { const done = sh.sent[t.k], busy = sh.busy[t.k]; return `<button class="shrow" data-a="${t.a}" data-x="${esc(t.x)}" ${off || done || busy ? 'disabled' : ''}>${t.av}<span class="grow b">${esc(t.name)}</span><span class="shsend ${done ? 'done' : ''}">${done ? 'Sent' : busy ? 'Sending…' : 'Send'}</span></button>`; }).join('')
      : `<div class="muted b" style="font-size:14px;padding:8px 0">Add friends to send it to them here.</div>`);
};
async function shSendTo(k, cidOf) {
  const sh = UI.share; if (!sh || !sh.link || sh.busy[k] || sh.sent[k]) return;
  sh.busy[k] = 1; render(true);
  const ok = await sh.ready, cid = ok ? await cidOf() : null, sent = cid ? await TC.send(cid, sh.body + ' ' + sh.link) : false;
  delete sh.busy[k];
  if (!ok) toast('Couldn’t get the link ready — try again');
  else if (sent) { sh.sent[k] = 1; toast('Sent'); }
  if (UI.share === sh) render(true);
}
/* A text message carrying one of our share links reads as a card with the picture on the phone.
   The link must be ours, on /s, with a 32-hex id — anything else stays plain text. */
const SH_RE = new RegExp('(?:^|\\s)' + String(WEB).replace(/\/+$/, '').replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&') + '\\/s\\?i=([0-9a-f]{32})\\.png(?:&[^\\s]*)?(?=\\s|$)');
function shMsg(m) {
  if (!m || (m.kind && m.kind !== 'text') || !m.body) return null;
  const hit = SH_RE.exec(m.body); if (!hit) return null;
  return { id: hit[1], text: m.body.replace(hit[0], ' ').replace(/\s+/g, ' ').trim() };
}
SHEETS.shareView = ({ id, from }) => `<div class="row sb"><h3>${esc(from && from !== TC.user.id ? nameOf(from).split(' ')[0] + '’s schedule' : 'Your schedule')}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <img class="shimg" src="${shImg(id)}" alt="A shared week of classes">
 ${from && TC.friends.includes(from) ? `<button class="btn soft" data-a="openFriend" data-x="${esc(from)}">See ${esc(nameOf(from).split(' ')[0])}’s profile</button>` : ''}`;
"""

R = [
 # the share icon
 ("chevR:'<path d=\"m9 5 7 7-7 7\"/>',chevL:'<path d=\"m15 5-7 7 7 7\"/>',",
  "chevR:'<path d=\"m9 5 7 7-7 7\"/>',chevL:'<path d=\"m15 5-7 7 7 7\"/>',share:'<path d=\"M12 15V3\"/><path d=\"m7 8 5-5 5 5\"/><path d=\"M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7\"/>',"),
 # the module, before the sheets
 ("const SHEETS = {};\n", "const SHEETS = {};\n" + JS.lstrip('\n')),
 # Plans: a Share button beside "Friends can see"
 ("<div class=\"regbar\"><span>${secs.length} class${secs.length === 1 ? '' : 'es'}</span><span class=\"regbadge\" style=\"background:var(--bg);color:var(--muted)\">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span></div>",
  "<div class=\"regbar\"><span>${secs.length} class${secs.length === 1 ? '' : 'es'}</span><span class=\"rgt\"><button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"${S.plan}\" aria-label=\"Share Plan ${S.plan}\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button><span class=\"regbadge\" style=\"background:var(--bg);color:var(--muted)\">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span></span></div>"),
 # My Classes: a Share button beside the class count
 ("<div class=\"regbar\" style=\"margin-top:14px\"><span>${esc(CFG.TERM_LABEL)}</span><span class=\"regbadge\">${Object.keys(byCode).length + unplaced.length} classes</span></div>",
  "<div class=\"regbar\" style=\"margin-top:14px\"><span>${esc(CFG.TERM_LABEL)}</span><span class=\"rgt\"><button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"mine\" aria-label=\"Share your week\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button><span class=\"regbadge\">${Object.keys(byCode).length + unplaced.length} classes</span></span></div>"),
 # actions
 ("  closeSheet: () => { UI.sheet = null; UI.champ = false; render(true); setBars(false); },\n",
  "  closeSheet: () => { UI.sheet = null; UI.champ = false; render(true); setBars(false); },\n"
  "  shareOpen: what => { if (!TC.seatsLoaded) { toast('Still loading your classes — try again in a moment'); return; } UI.sheet = { type: 'share' }; shPrepare(what === 'mine' || /^[ABC]$/.test(what) ? what : 'mine'); },\n"
  "  /* Called straight from the tap: iOS only opens its share sheet inside the gesture, so nothing is awaited here. */\n"
  "  shareLink: () => { const sh = UI.share; if (!sh || !sh.link || sh.state !== 'ready') return;\n"
  "    if (navigator.share) { navigator.share({ url: sh.link }).catch(() => {}); return; }\n"
  "    try { navigator.clipboard.writeText(sh.link).then(() => toast('Link copied'), () => toast(sh.link)); } catch (e) { toast(sh.link); } },\n"
  "  shareTo: uid => { if (TC.friends.includes(uid)) shSendTo('u:' + uid, () => TC.threadWith(uid)); },\n"
  "  shareToThread: cid => { if (TC.threads.some(t => t.id === cid)) shSendTo('t:' + cid, async () => cid); },\n"
  "  viewShare: (id, from) => { if (/^[0-9a-f]{32}$/.test(id)) { UI.sheet = { type: 'shareView', id, from }; render(true); } },\n"),
 # chat: a share-link message is a card
 ("    return `${sep}<div class=\"msg ${mine ? 'me' : ''}\">${showWho ? `<span class=\"who\">${esc(nameOf(m.sender).split(' ')[0])}</span>` : ''}${esc(msgText(m))}</div>`;",
  "    const shm = shMsg(m);\n"
  "    if (shm) return `${sep}<div class=\"msg shm ${mine ? 'me' : ''}\">${showWho ? `<span class=\"who\">${esc(nameOf(m.sender).split(' ')[0])}</span>` : ''}<button class=\"shcard\" data-a=\"viewShare\" data-x=\"${shm.id}\" data-y=\"${esc(m.sender)}\"><img src=\"${shImg(shm.id)}\" alt=\"A shared week of classes\" loading=\"lazy\"><span>${esc(shm.text || 'Shared a schedule')}</span></button></div>`;\n"
  "    return `${sep}<div class=\"msg ${mine ? 'me' : ''}\">${showWho ? `<span class=\"who\">${esc(nameOf(m.sender).split(' ')[0])}</span>` : ''}${esc(msgText(m))}</div>`;"),
 # thread previews: the sentence, not the long link
 ("function msgText(m) {\n  if (!m) return '';\n  if (m.body) return m.body;",
  "function msgText(m) {\n  if (!m) return '';\n  const shm = shMsg(m); if (shm) return shm.text || 'Shared a schedule';\n  if (m.body) return m.body;"),
 # styles
 (".regbadge{display:inline-flex;align-items:center;gap:5px;color:var(--teal);background:var(--teal-soft);font-weight:900;font-size:12.5px;padding:4px 10px;border-radius:12px}\n",
  ".regbadge{display:inline-flex;align-items:center;gap:5px;color:var(--teal);background:var(--teal-soft);font-weight:900;font-size:12.5px;padding:4px 10px;border-radius:12px}\n"
  "/* share your week or a plan (2026-09-30) */\n"
  ".regbar .rgt{display:flex;align-items:center;gap:8px}\n"
  ".shbtn[disabled]{opacity:.5}\n"
  ".shbtn{display:inline-flex;align-items:center;gap:5px;min-height:32px;padding:0 12px;border-radius:16px;background:var(--blue-soft);color:var(--blue-ink);font-weight:900;font-size:13px}\n"
  ".plancol .shbtn{background:var(--pc-soft);color:var(--pc-ink)}\n"
  ".shimg{display:block;width:100%;aspect-ratio:1/1;border-radius:18px;margin:12px 0;background:#F4F6FB;box-shadow:0 1px 3px rgba(15,23,42,.12)}\n"
  ".shwait{display:grid;place-items:center}\n"
  ".btn.shgo{display:flex;align-items:center;justify-content:center;gap:8px}\n"
  ".btn.shgo[disabled],.shrow[disabled]{opacity:.55}\n"
  ".shrow{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;padding:8px 0;border-top:1px solid var(--line);text-align:left}\n"
  ".shsend{flex:none;min-width:64px;text-align:center;padding:7px 12px;border-radius:14px;background:var(--blue);color:#fff;font-weight:900;font-size:13px}\n"
  ".shsend.done{background:var(--bg);color:var(--muted)}\n"
  ".msg.shm{padding:6px}\n"
  ".shcard{display:block;width:210px;max-width:100%;border-radius:14px;overflow:hidden;background:#fff;text-align:left}\n"
  ".shcard img{width:100%;aspect-ratio:1/1;background:#F4F6FB}\n"
  ".shcard span{display:block;padding:8px 10px;font-weight:800;font-size:13.5px;line-height:1.3;color:var(--ink)}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
